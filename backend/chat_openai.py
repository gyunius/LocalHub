from fastapi import APIRouter, HTTPException, Request
import os, asyncio, time
from collections import deque
import re

try:
    import openai
    AsyncOpenAI = getattr(openai, "AsyncOpenAI", None)
    OpenAI = getattr(openai, "OpenAI", None)
except Exception:
    openai = None
    AsyncOpenAI = None
    OpenAI = None

from pydantic import BaseModel
import logging, json
import traceback
from uuid import uuid4
from typing import Optional, List

from .models import POI
from sqlalchemy import select, text
from .main import AsyncSessionLocal

router = APIRouter()

logger = logging.getLogger("chat_openai")

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
# Tunable limits (can be overridden via environment variables)
OPENAI_MAX_OUTPUT_TOKENS = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS") or 4096)
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT") or 60)
PARSER_MAX_OUTPUT_TOKENS = int(os.getenv("PARSER_MAX_OUTPUT_TOKENS") or 512)
PARSER_TIMEOUT = float(os.getenv("PARSER_TIMEOUT") or 3.0)
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
    extracted_keywords = None
    extracted_keywords_text = None
    if req.use_search:
        q = req.message
        top_k = min(max(1, int(req.top_k or 5)), 50)
        # Parser: extract addr fragment and keywords (minimal JSON-only response)
        parser_model = os.getenv("PARSER_MODEL") or "gpt-4o-mini"
        parser_timeout = float(os.getenv("PARSER_TIMEOUT") or PARSER_TIMEOUT)
        parser_raw = None
        parser_json = None
        extracted_keywords = None
        extracted_keywords_text = None
        addr_fragment = None
        # Try LLM parser first (uses kw_system_prompt.txt when available); fallback to heuristics
        parser_raw = None
        parser_json = None
        if OPENAI_API_KEY and OpenAI is not None:
            try:
                prompt_path = os.path.join(os.path.dirname(__file__), "kw_system_prompt.txt")
                try:
                    with open(prompt_path, "r", encoding="utf-8") as pf:
                        parser_system = pf.read()
                except Exception:
                    parser_system = (
                        "당신은 입력 문장에서 주소(주소 일부)와 핵심 검색어를 추출하는 파서입니다.\n"
                        "반드시 JSON으로만 응답하세요. 형식: {\"addr\": \"주소 일부 또는 null\", \"search_keywords\": [\"키워드1\"]}\n"
                        "다른 설명은 포함하지 마세요."
                    )
                parser_user = f"질문: {q}\n\n응답은 반드시 JSON만 반환하세요."

                def sync_parser_call():
                    client2 = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAI()
                    is_modern = 'gpt-5' in parser_model or 'gpt-4o' in parser_model
                    if is_modern and hasattr(client2, 'responses'):
                        return client2.responses.create(model=parser_model, input=[{"role":"system","content":parser_system},{"role":"user","content":parser_user}], max_output_tokens=PARSER_MAX_OUTPUT_TOKENS)
                    token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                    kwargs = {token_param: PARSER_MAX_OUTPUT_TOKENS}
                    if not is_modern:
                        kwargs['temperature'] = 0.0
                    return client2.chat.completions.create(model=parser_model, messages=[{"role":"system","content":parser_system},{"role":"user","content":parser_user}], **kwargs)

                try:
                    resp = await asyncio.wait_for(asyncio.to_thread(sync_parser_call), timeout=parser_timeout)
                except Exception:
                    resp = None

                if resp is not None:
                    out_text = getattr(resp, 'output_text', None) or (resp.get('output_text') if isinstance(resp, dict) else None)
                    if not out_text:
                        ch = getattr(resp, 'choices', None) or (resp.get('choices') if isinstance(resp, dict) else None)
                        if ch:
                            first = ch[0]
                            msg = getattr(first, 'message', None) or (first.get('message') if isinstance(first, dict) else None)
                            if msg:
                                out_text = getattr(msg, 'content', None) or (msg.get('content') if isinstance(msg, dict) else None)
                            else:
                                out_text = getattr(first, 'text', None) or (first.get('text') if isinstance(first, dict) else None)
                    parser_raw = str(out_text).strip() if out_text else None
                    if parser_raw:
                        b = parser_raw.find('{')
                        e = parser_raw.rfind('}')
                        js = parser_raw[b:e+1] if b != -1 and e != -1 and e > b else parser_raw
                        try:
                            parser_json = json.loads(js)
                        except Exception:
                            parser_json = None
            except Exception:
                parser_raw = None
                parser_json = None

        # Heuristic parsing: detect a Seoul gu in the query and extract core Korean tokens as keywords
        seoul_gu = [
            '종로구','중구','용산구','성동구','광진구','동대문구','중랑구','성북구','강북구','도봉구',
            '노원구','은평구','서대문구','마포구','양천구','강서구','구로구','금천구','영등포구','동작구',
            '관악구','서초구','강남구','송파구','강동구'
        ]
        addr_fragment = None
        for g in seoul_gu:
            if g in q:
                addr_fragment = g
                break

        extracted_keywords = re.findall(r'[가-힣]{2,}', q)
        if addr_fragment and addr_fragment in extracted_keywords:
            extracted_keywords = [t for t in extracted_keywords if t != addr_fragment]
        # basic stopwords cleanup
        stopwords = set(['추천', '해주세요', '해줘', '제외', '추천해줘', '주세요'])
        extracted_keywords = [t for t in extracted_keywords if t not in stopwords][:3]
        extracted_keywords_text = None

        # Run simple LIKE-based SQL search using addr first, then keywords; rank by keyword overlap
        async with AsyncSessionLocal() as session:
            sources = []
            try:
                contentids = []
                if addr_fragment:
                    pattern = f"%{addr_fragment}%"
                    sql = text("SELECT contentid FROM poi WHERE addr1 LIKE :p LIMIT :lim")
                    res = await session.execute(sql.bindparams(p=pattern, lim=top_k))
                    contentids = [row[0] for row in res.fetchall()]

                if not contentids:
                    found = []
                    for kw in extracted_keywords:
                        if not kw:
                            continue
                        pattern = f"%{kw}%"
                        like_sql = text("SELECT contentid FROM poi WHERE title LIKE :p OR addr1 LIKE :p OR raw_json LIKE :p LIMIT :lim")
                        r2 = await session.execute(like_sql.bindparams(p=pattern, lim=top_k))
                        for row in r2.fetchall():
                            cid = row[0]
                            if cid not in found:
                                found.append(cid)
                                if len(found) >= top_k:
                                    break
                        if len(found) >= top_k:
                            break
                    contentids = found

                if contentids:
                    stmt = select(POI).where(POI.contentid.in_(contentids)).limit(top_k)
                    r = await session.execute(stmt)
                    rows = r.scalars().all()
                    scored = []
                    for p in rows:
                        textblob = ((p.title or '') + ' ' + (p.raw_json or '')).lower()
                        score = 0
                        for kw in extracted_keywords:
                            if kw and kw.lower() in textblob:
                                score += 1
                        scored.append((score, p))
                    scored.sort(key=lambda x: x[0], reverse=True)
                    final_rows = [p for s, p in scored][:min(5, len(scored))]
                    for p in final_rows:
                        sources.append({
                            'contentid': p.contentid,
                            'title': p.title,
                            'addr1': p.addr1,
                            'mapx': p.mapx,
                            'mapy': p.mapy,
                            'score': None,
                        })
                    search_path = 'simple_like'
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
            "간결하게 답하세요. 로컬 출처가 없을 경우 외부 추정 정보는 '[추정]'으로 표기하세요. "
            "각 추천은 불릿(-)으로 시작하는 한 문장으로 작성하고, 추천 검색어(2~3개), 대체 장소 유형(1개), 방문 팁(한 줄)을 포함하세요. "
            "마지막 줄에 '사용된 출처: 없음'을 표기하세요."
        )
        user_prompt = (
            f"질문: {req.message}\n\n"
            f"출처 목록:\n{sources_text}\n\n"
            "요청: 한국어로 간결하게 답하세요. 항목은 불릿(-)으로 시작하고 각 항목은 한 문장으로 구성하세요. "
            "출처가 없을 경우, 외부 추정 정보는 '[추정]'으로 표기하고, 추천 검색어(2~3개), 대체 장소 유형, 방문 팁(한 줄)을 반드시 제공하세요."
        )
    else:
        system_prompt = (
            "간결하고 근거 기반으로 답하세요. 제공된 로컬 출처만 사용하고 외부 지식이나 추측을 사용하지 마세요. "
            "각 항목은 불릿(-)으로 시작하는 한 문장으로 작성하고, 출처를 사용했으면 마지막 줄에 '사용된 출처: [contentid,...]'를 표기하세요."
        )
        user_prompt = (
            f"질문: {req.message}\n\n"
            f"출처 목록:\n{sources_text}\n\n"
            "요청: 한국어로 간결하게 답하세요. 항목은 불릿(-)으로 시작하고 각 항목은 한 문장으로 구성하세요. "
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
                                    resp = await asyncio.wait_for(c.responses.create(model=OPENAI_MODEL, input=messages, max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS), timeout=OPENAI_TIMEOUT)
                                else:
                                    token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                                    kwargs = {token_param: OPENAI_MAX_OUTPUT_TOKENS}
                                    if not is_modern:
                                        kwargs['temperature'] = 0.6
                                    resp = await asyncio.wait_for(c.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs), timeout=OPENAI_TIMEOUT)
                        else:
                            is_modern = 'gpt-5' in OPENAI_MODEL or 'gpt-4o' in OPENAI_MODEL
                            if is_modern and hasattr(client, 'responses'):
                                resp = await asyncio.wait_for(client.responses.create(model=OPENAI_MODEL, input=messages, max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS), timeout=OPENAI_TIMEOUT)
                            else:
                                token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                                kwargs = {token_param: OPENAI_MAX_OUTPUT_TOKENS}
                                if not is_modern:
                                    kwargs['temperature'] = 0.6
                                resp = await asyncio.wait_for(client.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs), timeout=OPENAI_TIMEOUT)
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
                                return client.responses.create(model=OPENAI_MODEL, input=user_prompt, max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS)
                            token_param = 'max_completion_tokens' if is_modern else 'max_tokens'
                            kwargs = {token_param: OPENAI_MAX_OUTPUT_TOKENS}
                            if not is_modern:
                                kwargs['temperature'] = 0.6
                            return client.chat.completions.create(model=OPENAI_MODEL, messages=messages, **kwargs)
                        resp = await asyncio.wait_for(asyncio.to_thread(sync_call), timeout=OPENAI_TIMEOUT)
                    except Exception as ex:
                        last_exc = traceback.format_exc()
                        resp = None

                # Do not call legacy openai.ChatCompletion for openai>=1.0; rely on AsyncOpenAI/OpenAI
                # If neither client produced a response, raise to outer handler and report error
                if resp is None:
                    raise RuntimeError(last_exc or "no compatible OpenAI client available or client call failed")

                # Log raw OpenAI response for debugging (serialize when possible)
                try:
                    def _serialize_resp(r):
                        try:
                            if isinstance(r, dict):
                                return json.dumps(r, ensure_ascii=False, default=str)
                            if hasattr(r, 'to_dict'):
                                return json.dumps(r.to_dict(), ensure_ascii=False, default=str)
                            d = {}
                            for k in ('model', 'output_text', 'choices', 'output'):
                                try:
                                    v = getattr(r, k, None)
                                except Exception:
                                    v = None
                                d[k] = v
                            return json.dumps(d, ensure_ascii=False, default=str)
                        except Exception:
                            return repr(r)
                    serialized = _serialize_resp(resp)
                    logger.info("openai_raw_response", extra={"extra": {"raw_response": serialized}})
                    try:
                        model_meta['raw_response'] = serialized
                    except Exception:
                        pass
                except Exception:
                    # don't let logging break normal flow
                    pass

                # Parse response robustly for different client types
                # update model_meta rather than overwrite to preserve debug fields
                try:
                    model_meta.update({"provider":"openai","model": getattr(resp, 'model', OPENAI_MODEL)})
                except Exception:
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
    # If model produced no usable text, generate a safe server-side fallback
    def _make_fallback(query: str, sources_present: bool):
        q = query or ""
        # simple heuristics to build fallback suggestions
        keywords = []
        try:
            parts = q.replace('?', '').replace('.', '').split()
            # take up to 2 non-stopword tokens
            for p in parts:
                if len(keywords) >= 2:
                    break
                if len(p) > 1:
                    keywords.append(p)
        except Exception:
            keywords = []
        if not keywords:
            keywords = ["서울", "추천"]
        rec_search = ", ".join(keywords[:2])
        items = []
        if sources_present:
            items.append("- 제공된 로컬 출처를 기준으로 관련 장소를 확인해보세요. [추정]")
        else:
            items.append(f"- [추정] {keywords[0]} 인근의 유명한 관광지나 공원, 전망대를 고려해보세요.")
            items.append(f"- [추정] 박물관이나 실내 체험형 전시도 가족 방문에 좋습니다.")
            items.append(f"- [추정] 날씨와 혼잡도를 고려해 평일 낮 방문을 권합니다.")
        tip_line = f"추천 검색어: {rec_search}"
        alt_line = "대체 장소 유형: 박물관, 실내 체험관"
        visit_tip = "방문 팁: 가능하면 평일 낮 방문이나 사전 예매를 권합니다. [추정]"
        body = "\n".join(items + ["", tip_line, alt_line, visit_tip, "", "사용된 출처: 없음"]) if not sources_present else "\n".join(items + ["", tip_line, alt_line, visit_tip, "", "사용된 출처: [provided]"])
        return body

    if not openai_resp_text or openai_resp_text.strip() == "":
        fallback = _make_fallback(req.message, bool(sources))
        reply_text = fallback
        try:
            model_meta['fallback'] = True
        except Exception:
            pass

    # include extracted keywords (if any) in model_meta for debugging/client display
    try:
        if extracted_keywords is not None:
            model_meta['extracted_keywords'] = extracted_keywords
    except Exception:
        pass
    try:
        if extracted_keywords_text is not None:
            model_meta['extracted_keywords_text'] = extracted_keywords_text
    except Exception:
        pass
    try:
        if 'search_path' in locals() and search_path is not None:
            model_meta['search_path'] = search_path
    except Exception:
        pass

    # Attach concise debug info to `model_meta`
    try:
        if extracted_keywords is not None:
            model_meta['extracted_keywords'] = extracted_keywords
    except Exception:
        pass
    try:
        if extracted_keywords_text is not None:
            model_meta['extracted_keywords_text'] = extracted_keywords_text
    except Exception:
        pass
    try:
        if addr_fragment:
            model_meta['addr_fragment'] = addr_fragment
    except Exception:
        pass
    try:
        if 'search_path' in locals() and search_path is not None:
            model_meta['search_path'] = search_path
    except Exception:
        pass
    try:
        if parser_raw is not None:
            model_meta['parser_raw'] = parser_raw
    except Exception:
        pass
    try:
        if parser_json is not None:
            model_meta['parser_json'] = parser_json
    except Exception:
        pass

    return {"id": resp_id, "reply": reply_text, "sources": sources, "session_id": session_id, "model_meta": model_meta}
