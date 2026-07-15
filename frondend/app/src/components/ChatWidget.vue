<template>
  <div class="chat-widget surface-card">
    <div class="panel-header">
      <div>
        <div class="eyebrow">Assistant</div>
        <h3 class="panel-title">지역 질문 챗봇</h3>
      </div>
    </div>

    <div class="chat-body">
      <div v-if="loading" class="chat-loading">응답 생성 중...</div>

      <div v-if="reply" class="chat-reply" v-html="escapedReply"></div>

      <div v-if="sources.length" class="sources-list">
        <h4 class="sources-title">참고 출처</h4>
        <ul>
          <li v-for="s in sources" :key="s.contentid" :class="{'source-used': s.used}">
            <div class="source-row">
              <div class="source-meta">
                <strong>{{ s.title || s.contentid }}</strong>
                <div class="source-addr">{{ s.addr1 }}</div>
              </div>
              <div class="source-actions">
                <a :href="`/places/${s.contentid}`" class="link">상세</a>
                <span v-if="s.used" class="used-badge">참조됨</span>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <div class="chat-input">
      <textarea v-model="message" placeholder="질문을 입력하세요" rows="2"></textarea>
      <div class="actions">
        <button class="btn" :class="{'btn-primary': !loading}" @click="send" :disabled="loading || !message.trim()">전송</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const message = ref('')
const loading = ref(false)
const reply = ref('')
const sources = ref<any[]>([])

const escapeHtml = (unsafe: string) => {
  return (unsafe || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const escapedReply = computed(() => {
  // basic line breaks to <br>, preserve text safety
  return escapeHtml(reply.value).replace(/\n/g, '<br/>')
})

async function send() {
  if (!message.value.trim()) return
  loading.value = true
  reply.value = ''
  sources.value = []

  try {
    const res = await fetch('/api/chat_openai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message.value, use_search: true })
    })
    if (!res.ok) throw new Error('응답 실패')
    const data = await res.json()
    reply.value = data.reply || ''
    // normalize sources: ensure used field exists
    sources.value = (data.sources || []).map((s: any) => ({ ...s, used: !!s.used }))
  } catch (err) {
    reply.value = '[오류] 응답을 가져오지 못했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.chat-widget { padding: 12px; display:flex; flex-direction:column; gap:10px }
.panel-header { display:flex; align-items:center; justify-content:space-between }
.chat-body { min-height: 120px }
.chat-loading { color: #6b6b6b }
.chat-reply { white-space: pre-wrap; margin-bottom:8px }
.sources-list { margin-top:8px }
.sources-title { font-size:13px; margin-bottom:6px }
.source-row { display:flex; align-items:center; justify-content:space-between; padding:8px; border-radius:8px }
.source-used { background: linear-gradient(90deg,#f0f7ff,#eef9f8) }
.used-badge { background:#e6f6ea; color:#1b7f3a; padding:3px 6px; border-radius:10px; font-size:12px }
.chat-input textarea { width:100%; padding:8px; border-radius:8px; border:1px solid #e6e6e6 }
.actions { margin-top:6px; display:flex; justify-content:flex-end }
.btn { padding:8px 12px; border-radius:8px; border:1px solid #ccc; background:#fff }
.btn-primary { background:linear-gradient(90deg,#6b3bb4,#4b65bf); color:#fff; border:none }
</style>
