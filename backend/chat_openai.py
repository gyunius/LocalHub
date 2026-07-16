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

    # If search requested but no local sources found, allow model call
    # but instruct model to clearly mark any external/estimated info as [추정]
    no_local_sources = req.use_search and not sources

    # Build prompts; when no local sources exist, allow safe estimated suggestions.
    if no_local_sources:
        system_prompt = (
            "당신은 서울 지역 정보에 전문적인 한국어 가이드입니다. 질문에 대해 간결하고 정확하게 답하세요. "
            "로컬 출처가 제공되지 않을 때는, 모델이 합리적으로 '추정'하는 정보를 제공할 수 있습니다. "
            "모든 외부 추정 정보 또는 불확실한 내용은 반드시 '[추정]'으로 표기하세요. "
            "로컬 출처를 사용한 경우에는 출처(contentid)를 명시하세요. "
            "로컬 출처가 없을 때는 불확실성을 명시한 안전한 제안(추천 검색어 2~3개, 대체 장소 유형, 방문 팁 한 줄)을 반드시 포함하세요. "
            "답변은 최대 3개의 항목(또는 1~3문장)으로 요약하고, 마지막 줄에 '사용된 출처: [contentid,...]' 또는 '사용된 출처: 없음'을 표기하세요."
        )
        user_prompt = (
            f"질문: {req.message}\n\n"
            f"출처 목록:\n{sources_text}\n\n"
            "요청: 한국어로 간결하게 답변하세요. 항목은 불릿(-)으로 시작하고 각 항목은 한 문장으로 구성하세요. "
            "출처가 없을 경우, 외부 추정 정보는 '[추정]'으로 표기하고, 추천 검색어(2~3개), 대체 장소 유형, 방문 팁(한 줄)을 반드시 제공하세요."
        )
    else:
        system_prompt = (
            "당신은 서울 지역 정보에 전문적인 한국어 가이드입니다. 질문에 대해 간결하고 정확하게 답하고, "
            "오직 제공된 로컬 출처만 사용하여 근거 있는 답변만 하세요. 외부의 지식이나 추측은 사용하지 마세요. "
            "답변은 최대 3개의 항목(또는 1~3문장)으로 요약하고, 마지막 줄에 '사용된 출처: [contentid,...]' 형태로 표기하세요."
        )
        user_prompt = (
            f"질문: {req.message}\n\n"
            f"출처 목록:\n{sources_text}\n\n"
            "요청: 한국어로 간결하게 답변하세요. 항목은 불릿(-)으로 시작하고 각 항목은 한 문장으로 구성하세요. "
            "출처를 사용했으면 본문 끝에 사용된 출처의 contentid를 대괄호로 나열하세요. 출처가 없다면 '사용된 출처: 없음'을 쓰세요."
        )
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
                                    # Responses API: pass messages list as `input` for chat-style models
                                    resp = await asyncio.wait_for(c.responses.create(model=OPENAI_MODEL, input=messages, max_output_tokens=1024), timeout=30)
                                else:
                                    token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                                    kwargs = {token_param: 350}
                                    if not is_modern:
                                        kwargs['temperature'] = 0.6
                                    resp = await asyncio.wait_for(c.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs), timeout=30)
                        else:
                            is_modern = 'gpt-5' in OPENAI_MODEL or 'gpt-4o' in OPENAI_MODEL
                            if is_modern and hasattr(client, 'responses'):
                                resp = await asyncio.wait_for(client.responses.create(model=OPENAI_MODEL, input=messages, max_output_tokens=1024), timeout=30)
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
                openai_resp_text = ""
                # Responses API may provide `output_text` or `output` array
                try:
                    out_text = getattr(resp, 'output_text', None) or (resp.get('output_text') if isinstance(resp, dict) else None)
                except Exception:
                    out_text = None
                if out_text:
                    openai_resp_text = str(out_text).strip()
                else:
                    # try choices (chat.completions style)
                    content = None
                    choices = None
                    try:
                        choices = getattr(resp, 'choices', None) or (resp.get('choices') if isinstance(resp, dict) else None)
                    except Exception:
                        choices = None
                    if choices:
                        first = choices[0]
                        msg = None
                        try:
                            msg = getattr(first, 'message', None) or (first.get('message') if isinstance(first, dict) else None)
                        except Exception:
                            msg = None
                        if msg:
                            content = getattr(msg, 'content', None) or (msg.get('content') if isinstance(msg, dict) else None)
                        else:
                            content = getattr(first, 'text', None) or (first.get('text') if isinstance(first, dict) else None)
                        openai_resp_text = (content or "").strip()
                    else:
                        # try Responses API detailed output structure
                        try:
                            out = getattr(resp, 'output', None) or (resp.get('output') if isinstance(resp, dict) else None)
                        except Exception:
                            out = None
                        if out:
                            parts = []
                            for item in out:
                                # each item may have 'content' array
                                cont = item.get('content') if isinstance(item, dict) else None
                                if cont and isinstance(cont, list):
                                    for c in cont:
                                        if isinstance(c, dict):
                                            text = c.get('text') or c.get('payload') or None
                                            if text:
                                                parts.append(text)
                                        elif isinstance(c, str):
                                            parts.append(c)
                            openai_resp_text = "\n".join(parts).strip()
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
