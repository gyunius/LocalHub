<template>
  <div class="chatbot-floating" aria-hidden="false">

    <transition name="chatbot-fade">
      <div v-if="open" class="chatbot-panel" role="dialog" aria-label="Chatbot window">
        <div class="chatbot-header">
          <strong>LocalHub 챗봇</strong>
          <button class="close-btn" @click="toggle" aria-label="Close">×</button>
        </div>
        <div ref="bodyRef" class="chatbot-body">
          <ul class="chat-list">
            <li v-for="m in messages" :key="m.id" :class="['msg', m.role]">
              <div v-if="!m.pending" class="msg-text">{{ m.text }}</div>
              <div v-else class="msg-cot">
                <div v-if="m.cot && m.cot.length">
                  <div v-for="(line, i) in m.cot" :key="i" class="cot-line">{{ line }}</div>
                </div>
                <div v-else class="cot-line placeholder">생각 중...</div>
              </div>
              <div v-if="m.role === 'assistant' && !m.pending && m.sources && m.sources.length" class="msg-sources">
                <div class="sources-title">출처:</div>
                <ul class="sources-list">
                  <li v-for="s in m.sources" :key="s.contentid" class="source-item">
                    <div class="source-line">
                      <strong class="source-title">{{ s.title || '무제' }}</strong>
                      <span class="source-id">[{{ s.contentid }}]</span>
                    </div>
                    <div class="source-addr" v-if="s.addr1">{{ s.addr1 }}</div>
                    <a v-if="s.mapx && s.mapy" :href="`https://www.google.com/maps?q=${s.mapy},${s.mapx}`" target="_blank" rel="noopener noreferrer" class="source-map-link">지도 보기</a>
                  </li>
                </ul>
              </div>
              <div v-if="m.role === 'assistant' && !m.pending && m.meta" class="msg-meta">
                <div v-if="m.meta.search_path" class="meta-line">검색: <span class="meta-val">{{ m.meta.search_path }}</span></div>
                <div v-if="m.meta.extracted_keywords && m.meta.extracted_keywords.length" class="meta-line">키워드: <span class="meta-val">{{ m.meta.extracted_keywords.join(', ') }}</span></div>
              </div>
            </li>
          </ul>
        </div>
        <div class="chatbot-input">
          <textarea
            v-model="message"
            placeholder="메시지 입력 (예: 근처 맛집 추천)"
            @keydown="onKeydown"
            rows="2"
          ></textarea>
          <button @click="send" :disabled="sending">{{ sending ? '전송중...' : '전송' }}</button>
        </div>
      </div>
    </transition>

    <button class="chatbot-button" @click="toggle" aria-label="Open chat">
      <svg viewBox="0 0 24 24" width="28" height="28" fill="none" aria-hidden="true">
        <rect x="3" y="7" width="18" height="11" rx="2" stroke="currentColor" stroke-width="1.2" fill="currentColor" opacity="0.12" />
        <rect x="8" y="3" width="8" height="4" rx="1" stroke="currentColor" stroke-width="1.2" fill="currentColor" opacity="0.1" />
        <circle cx="8.5" cy="12.5" r="1.1" fill="currentColor" />
        <circle cx="15.5" cy="12.5" r="1.1" fill="currentColor" />
        <path d="M9 20v1M15 20v1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

type POISource = { contentid: string; title?: string; addr1?: string; mapx?: number; mapy?: number; score?: number }
type ChatMessage = { id: string; role: string; text: string; sources?: POISource[]; pending?: boolean; cot?: string[]; meta?: any }

const open = ref(false)
const message = ref('')
const messages = ref<ChatMessage[]>([])
const sending = ref(false)
const bodyRef = ref<HTMLElement | null>(null)
const pendingTimers = ref<Record<string, number>>({})

function startCot(pendingId: string) {
  const steps = [
    '질문의 의도 파악 중...',
    '관련 POI 검색 중...',
    '출처 필터링 중...',
    '정보 요약 및 근거 정리 중...',
    '최종 답변 구성 중...'
  ]
  let stepIndex = 0
  const id = window.setInterval(() => {
    const idx = messages.value.findIndex(m => m.id === pendingId)
    if (idx < 0) return
    const m = messages.value[idx]
    if (!m.cot) m.cot = []
    m.cot = [...m.cot.slice(-2), steps[stepIndex % steps.length]]
    stepIndex += 1
  }, 1200)
  pendingTimers.value[pendingId] = id
}

function stopCot(pendingId: string) {
  const id = pendingTimers.value[pendingId]
  if (id) {
    clearInterval(id)
    delete pendingTimers.value[pendingId]
  }
}

const API_BASE = (import.meta.env.VITE_API_BASE as string) ?? '/api'
const SESSION_KEY = 'localhub.chat.session_id'
let sessionId = sessionStorage.getItem(SESSION_KEY)
if (!sessionId) {
  sessionId = `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,8)}`
  try { sessionStorage.setItem(SESSION_KEY, sessionId) } catch (e) {}
}

function toggle() {
  open.value = !open.value
  if (open.value) {
    // small delay to allow panel to render then scroll
    setTimeout(scrollToBottom, 50)
  }
}

function onKeydown(e: KeyboardEvent) {
  // don't trigger send when a request is in flight, but allow typing
  if (sending.value) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function scrollToBottom() {
  try {
    const el = (bodyRef.value as HTMLElement)
    if (!el) return
    el.scrollTop = el.scrollHeight
  } catch (e) {}
}

async function send() {
  const text = (message.value || '').trim()
  if (!text) return
  const userId = `u_${Date.now()}`
  messages.value.push({ id: userId, role: 'user', text })
  message.value = ''
  sending.value = true

  // placeholder assistant message (show CoT while waiting)
  const pendingId = `a_pending_${Date.now()}`
  messages.value.push({ id: pendingId, role: 'assistant', text: '', pending: true, cot: [] })
  await nextTick()
  scrollToBottom()
  startCot(pendingId)

  try {
    const resp = await fetch(`${API_BASE}/chat_openai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId })
    })
    const data = await resp.json().catch(() => ({}))
    const reply = (data && data.reply) ? String(data.reply) : (resp.ok ? '[응답 없음]' : `오류: ${resp.status}`)
    const sources = (data && Array.isArray(data.sources)) ? data.sources : []
    const meta = (data && data.model_meta) ? data.model_meta : undefined
    const idx = messages.value.findIndex(m => m.id === pendingId)
    if (idx >= 0) {
      stopCot(pendingId)
      messages.value[idx].text = reply
      messages.value[idx].sources = sources
      messages.value[idx].meta = meta
      messages.value[idx].pending = false
      messages.value[idx].cot = []
    } else {
      messages.value.push({ id: `a_${Date.now()}`, role: 'assistant', text: reply, sources, meta })
    }
  } catch (err) {
    const idx = messages.value.findIndex(m => m.id === pendingId)
    const errText = '서버 연결 오류가 발생했습니다.'
    stopCot(pendingId)
    if (idx >= 0) {
      messages.value[idx].text = errText
      messages.value[idx].pending = false
      messages.value[idx].cot = []
    } else {
      messages.value.push({ id: `a_err_${Date.now()}`, role: 'assistant', text: errText })
    }
  } finally {
    sending.value = false
    await nextTick()
    scrollToBottom()
  }
}

onMounted(() => scrollToBottom())

// auto-scroll when messages change
watch(messages, async () => {
  await nextTick()
  scrollToBottom()
}, { deep: true })
</script>

<style scoped>
.chatbot-floating {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1200;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.chatbot-button {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #0ea5e9);
  color: white;
  display: grid;
  place-items: center;
  border: none;
  box-shadow: 0 8px 20px rgba(7, 89, 133, 0.16);
  cursor: pointer;
}

.chatbot-panel {
  width: 320px;
  max-width: calc(100vw - 40px);
  margin-bottom: 12px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.12);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chatbot-header {
  padding: 10px 12px;
  background: linear-gradient(90deg,#0369a1,#0ea5e9);
  color: white;
  display:flex;
  align-items:center;
  justify-content:space-between;
}

.chatbot-body { padding: 12px; min-height: 110px; max-height: 260px; overflow:auto; }
.chat-list { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px }
.msg { max-width: 84%; padding:8px 10px; border-radius:10px; font-size:14px; line-height:1.4; white-space:pre-wrap }
.msg.user { align-self: flex-end; background: linear-gradient(90deg,#7dd3fc,#0ea5e9); color:#04263a }
.msg.assistant { align-self: flex-start; background:#f1f5f9; color:#0f172a }
.placeholder { color: #667085; font-size: 14px }

.chatbot-input { display:flex; gap:8px; padding:10px; border-top: 1px solid #f1f5f9; }
.chatbot-input textarea { flex:1; padding:8px 10px; border-radius:8px; border:1px solid #e6eef6; resize: none }
.chatbot-input button { padding:8px 12px; background:#0ea5e9; color:white; border:none; border-radius:8px; cursor:pointer }

.close-btn { background:transparent; border:none; color:white; font-size:18px; line-height:1; cursor:pointer }

/* simple transition */
.chatbot-fade-enter-active, .chatbot-fade-leave-active { transition: opacity .18s ease, transform .18s ease }
.chatbot-fade-enter-from { opacity: 0; transform: translateY(6px) }
.chatbot-fade-enter-to { opacity: 1; transform: translateY(0) }
.chatbot-fade-leave-from { opacity: 1; transform: translateY(0) }
.chatbot-fade-leave-to { opacity: 0; transform: translateY(6px) }
</style>

<style scoped>
.msg-sources { margin-top: 8px; padding: 8px; background: rgba(2,6,23,0.03); border-radius: 8px; }
.sources-title { font-size:12px; color:#334155; margin-bottom:6px; font-weight:600 }
.sources-list { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:6px }
.source-item { font-size:13px; color:#0f172a }
.source-line { display:flex; gap:8px; align-items:center }
.source-title { font-weight:600 }
.source-id { color:#64748b; font-size:12px }
.source-addr { color:#475569; font-size:12px }
.source-map-link { display:inline-block; margin-top:4px; color:#0ea5e9; font-size:12px }

.msg-meta { margin-top:8px; font-size:12px; color:#475569 }
.meta-line { margin-top:4px }
.meta-val { color:#0f172a; font-weight:600; margin-left:6px }
.msg-cot { margin-top: 8px; padding: 8px; background: rgba(2,6,23,0.03); border-radius: 8px; }
.cot-line { font-size:13px; color:#0f172a; line-height:1.3 }
.cot-line.placeholder { color:#64748b }
</style>
