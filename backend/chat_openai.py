from fastapi import APIRouter, HTTPException, Request
import os, asyncio, time
from collections import deque

try:
    import openai
except Exception:
    openai = None

from pydantic import BaseModel
from uuid import uuid4
from typing import Optional, List

from models import POI
from sqlalchemy import select, text
from main import AsyncSessionLocal

router = APIRouter()

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30
_counters = {}

async def _rate_limit_check(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    dq = _counters.get(ip)
    if dq is None:
        dq = deque()
        _counters[ip] = dq
    while dq and dq[0] <= now - RATE_LIMIT_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
    dq.append(now)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    top_k: Optional[int] = 5
    use_search: Optional[bool] = True

class POISource(BaseModel):
    contentid: str
    title: Optional[str] = None
    addr1: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None
    score: Optional[float] = None

class ChatResponse(BaseModel):
    id: str
    reply: str
    sources: List[POISource] = []
    session_id: Optional[str] = None
    model_meta: Optional[dict] = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY and openai:
    openai.api_key = OPENAI_API_KEY

@router.post("/api/chat_openai", response_model=ChatResponse)
async def chat_openai(req: ChatRequest, request: Request):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message required")
    await _rate_limit_check(request)

    resp_id = str(uuid4())
    session_id = req.session_id or resp_id
    sources = []
    if req.use_search:
        q = req.message
        top_k = min(max(1, int(req.top_k or 5)), 50)
        async with AsyncSessionLocal() as session:
            try:
                sql = text("SELECT contentid FROM poi_fts WHERE poi_fts MATCH :q LIMIT :lim")
                res = await session.execute(sql.bindparams(q=q, lim=top_k))
                contentids = [row[0] for row in res.fetchall()]
                if contentids:
                    stmt = select(POI).where(POI.contentid.in_(contentids)).limit(top_k)
                    r = await session.execute(stmt)
                    rows = r.scalars().all()
                    for p in rows:
                        sources.append({
                            "contentid": p.contentid,
                            "title": p.title,
                            "addr1": p.addr1,
                            "mapx": p.mapx,
                            "mapy": p.mapy,
                            "score": None,
                        })
            except Exception:
                sources = []

    if not (OPENAI_API_KEY and openai):
        return {"id": resp_id, "reply": f"[mock/openai-unavailable] 찾은 장소 수: {len(sources)}. 원문: {req.message[:200]}", "sources": sources, "session_id": session_id, "model_meta": {"mock": True, "openai_available": False}}

    sources_text = "\n".join([f"- {s['title']} ({s['contentid']}): {s.get('addr1') or ''}" for s in sources]) if sources else "(no sources)"
    system_prompt = "You are a helpful assistant recommending Seoul points of interest when asked. Use provided sources when relevant and cite them."
    user_prompt = f"User message: {req.message}\n\nSources:\n{sources_text}\n\nReply concisely and list used sources by contentid."
    messages = [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}]

    openai_resp_text = ""
    model_meta = {"provider":"openai","model":"unknown"}
    try:
        attempt = 0
        while attempt < 3:
            attempt += 1
            try:
                resp = await asyncio.wait_for(asyncio.to_thread(openai.ChatCompletion.create, model="gpt-3.5-turbo", messages=messages, max_tokens=350, temperature=0.6), timeout=12)
                model_meta = {"provider":"openai","model": getattr(resp, 'model', 'gpt-3.5-turbo')}
                choice = resp.choices[0] if getattr(resp, 'choices', None) else None
                content = None
                if choice:
                    if getattr(choice, 'message', None):
                        content = getattr(choice.message, 'content', None)
                    if not content:
                        content = getattr(choice, 'text', None)
                openai_resp_text = (content or "").strip()
                break
            except Exception:
                if attempt < 3:
                    await asyncio.sleep(1 * attempt)
                else:
                    raise
    except Exception as e:
        openai_resp_text = f"[openai error fallback] 찾은 장소 수: {len(sources)}. 원문: {req.message[:200]}"
        model_meta = {"error": str(e)}

    reply_text = openai_resp_text or f"[openai empty reply] 찾은 장소 수: {len(sources)}"
    return {"id": resp_id, "reply": reply_text, "sources": sources, "session_id": session_id, "model_meta": model_meta}
