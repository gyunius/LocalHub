from fastapi import APIRouter, HTTPException, Request
import os, asyncio, time
from collections import deque

try:
    import openai
    AsyncOpenAI = getattr(openai, "AsyncOpenAI", None)
    OpenAI = getattr(openai, "OpenAI", None)
except Exception:
    openai = None
    AsyncOpenAI = None
    OpenAI = None

from pydantic import BaseModel
import traceback
from uuid import uuid4
from typing import Optional, List

from .models import POI
from sqlalchemy import select, text
from .main import AsyncSessionLocal

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
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-5-mini"
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
        last_exc = None
        while attempt < 3:
            attempt += 1
            try:
                resp = None
                # Prefer async OpenAI client if available
                if AsyncOpenAI is not None:
                    try:
                        client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else AsyncOpenAI()
                        if hasattr(client, "__aenter__"):
                            async with client as c:
                                is_modern = 'gpt-5' in OPENAI_MODEL or 'gpt-4o' in OPENAI_MODEL
                                if is_modern and hasattr(c, 'responses'):
                                    # Responses API expects `input` instead of messages
                                    resp = await asyncio.wait_for(c.responses.create(model=OPENAI_MODEL, input=user_prompt, max_completion_tokens=350), timeout=30)
                                else:
                                    token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                                    kwargs = {token_param: 350}
                                    if not is_modern:
                                        kwargs['temperature'] = 0.6
                                    resp = await asyncio.wait_for(c.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs), timeout=30)
                        else:
                            is_modern = 'gpt-5' in OPENAI_MODEL or 'gpt-4o' in OPENAI_MODEL
                            if is_modern and hasattr(client, 'responses'):
                                resp = await asyncio.wait_for(client.responses.create(model=OPENAI_MODEL, input=user_prompt, max_completion_tokens=350), timeout=30)
                            else:
                                token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                                kwargs = {token_param: 350}
                                if not is_modern:
                                    kwargs['temperature'] = 0.6
                                resp = await asyncio.wait_for(client.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs), timeout=30)
                    except Exception as ex:
                        last_exc = traceback.format_exc()
                        resp = None

                # If async client not available, try sync OpenAI client (run in thread)
                if resp is None and OpenAI is not None:
                    try:
                        def sync_call():
                            client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAI()
                            is_modern = 'gpt-5' in OPENAI_MODEL or 'gpt-4o' in OPENAI_MODEL
                            if is_modern and hasattr(client, 'responses'):
                                return client.responses.create(model=OPENAI_MODEL, input=user_prompt, max_completion_tokens=350)
                            token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                            kwargs = {token_param: 350}
                            if not is_modern:
                                kwargs['temperature'] = 0.6
                            return client.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs)
                        resp = await asyncio.wait_for(asyncio.to_thread(sync_call), timeout=30)
                    except Exception as ex:
                        last_exc = traceback.format_exc()
                        resp = None

                # Do not call legacy openai.ChatCompletion for openai>=1.0; rely on AsyncOpenAI/OpenAI
                # If neither client produced a response, raise to outer handler and report error
                if resp is None:
                    raise RuntimeError(last_exc or "no compatible OpenAI client available or client call failed")

                # Parse response robustly for different client types
                model_meta = {"provider":"openai","model": getattr(resp, 'model', OPENAI_MODEL)}
                content = None
                # resp may be a mapping or object with .choices
                choices = None
                try:
                    choices = getattr(resp, 'choices', None) or (resp.get('choices') if isinstance(resp, dict) else None)
                except Exception:
                    choices = None
                if choices:
                    first = choices[0]
                    # try different shapes
                    msg = None
                    try:
                        msg = getattr(first, 'message', None) or (first.get('message') if isinstance(first, dict) else None)
                    except Exception:
                        msg = None
                    if msg:
                        content = getattr(msg, 'content', None) or (msg.get('content') if isinstance(msg, dict) else None)
                    else:
                        # older style
                        content = getattr(first, 'text', None) or (first.get('text') if isinstance(first, dict) else None)
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
