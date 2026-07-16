<template>
  <div class="post-detail-page">
    <button
      v-if="!props.embedded"
      type="button"
      class="back-link"
      @click="$router.back()"
    >
      <svg
        viewBox="0 0 24 24"
        width="17"
        height="17"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="m15 5-7 7 7 7"
          stroke="currentColor"
          stroke-width="1.9"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>

      목록으로 돌아가기
    </button>

    <button
      v-else
      type="button"
      class="back-link"
      @click="onClose"
    >
      <svg
        viewBox="0 0 24 24"
        width="17"
        height="17"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="m15 5-7 7 7 7"
          stroke="currentColor"
          stroke-width="1.9"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>

      닫기
    </button>

    <div
      v-if="loading"
      class="surface-card post-loading"
    >
      <div class="loading-ring"></div>
      <p>이야기를 불러오는 중이에요.</p>
    </div>

    <div
      v-else-if="error"
      class="alert alert-error"
    >
      <svg
        viewBox="0 0 24 24"
        width="19"
        height="19"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M12 8v5m0 3.2v.1M10.3 4.5 3.4 17a2 2 0 0 0 1.75 3h13.7a2 2 0 0 0 1.75-3L13.7 4.5a2 2 0 0 0-3.4 0Z"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        />
      </svg>

      {{ error }}
    </div>

    <article
      v-else-if="post"
      class="post-article surface-card"
    >
      <header class="article-header">
        <div class="eyebrow">Travel story</div>

        <h1>{{ post.title }}</h1>

        <div class="article-meta">
          <span>
            <svg
              viewBox="0 0 24 24"
              width="15"
              height="15"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M7 3v3m10-3v3M4.5 9h15M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Z"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>

            {{ formatDate(post.created_at) }}
          </span>

          <span v-if="post.views !== undefined">
            <svg
              viewBox="0 0 24 24"
              width="15"
              height="15"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M2.8 12s3.3-5.5 9.2-5.5 9.2 5.5 9.2 5.5-3.3 5.5-9.2 5.5S2.8 12 2.8 12Z"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linejoin="round"
              />

              <circle
                cx="12"
                cy="12"
                r="2.4"
                stroke="currentColor"
                stroke-width="1.7"
              />
            </svg>

            {{ post.views }}회
          </span>
        </div>
      </header>

      <img
        v-if="post.firstimage"
        :src="post.firstimage"
        :alt="post.title"
        class="article-image"
      />

      <div class="article-body">
        <p>{{ post.content }}</p>
      </div>

      <footer class="article-footer">
        <p>
          이 게시글은 작성 시 설정한 비밀번호로 수정하거나
          삭제할 수 있습니다.
        </p>

        <div class="article-actions">
          <button
            type="button"
            class="btn btn-secondary"
            @click="startAction('edit')"
          >
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="m14.5 5.5 4 4M4 20l4.1-.9L19 8.2a1.4 1.4 0 0 0 0-2l-1.2-1.2a1.4 1.4 0 0 0-2 0L4.9 15.9 4 20Z"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>

            수정
          </button>

          <button
            type="button"
            class="btn btn-danger"
            @click="startAction('delete')"
          >
            <svg
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M4 7h16M9 3h6l1 4H8l1-4Zm-3 4 1 14h10l1-14M10 11v6m4-6v6"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>

            삭제
          </button>
        </div>
      </footer>
    </article>

    <PasswordModal
      :show="showPw"
      title="비밀번호를 입력하세요"
      @update:show="showPw = $event"
      @confirm="onConfirmPassword"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PasswordModal from '../components/PasswordModal.vue'

import {
  deletePost,
  fetchPost,
  verifyPostPassword,
} from '../services/postService'

const props = defineProps<{ embedded?: boolean; id?: string }>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit-post', id: string): void
}>()

const route = useRoute()
const router = useRouter()

const id = String(props.id ?? String(route.params.id ?? ''))

const post = ref<any>(null)
const loading = ref(true)
const error = ref('')
const showPw = ref(false)

let pendingAction: 'edit' | 'delete' | null = null

onMounted(async () => {
  try {
    post.value = await fetchPost(id)
    try { emit('show-route', (post.value as any).route ?? []) } catch (e) {}
  } catch (caughtError) {
    error.value = (caughtError as Error).message
  } finally {
    loading.value = false
  }
})

function formatDate(value?: string) {
  if (!value) {
    return ''
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return `${date.getFullYear()}년 ${
    date.getMonth() + 1
  }월 ${date.getDate()}일`
}

function startAction(action: 'edit' | 'delete') {
  error.value = ''
  pendingAction = action
  showPw.value = true
}

function onClose() {
  try { emit('close') } catch (e) {}
}

async function onConfirmPassword(password: string) {
  if (!pendingAction) {
    return
  }

  if (pendingAction === 'edit') {
    try {
      const verified = await verifyPostPassword(
        id,
        password,
      )

      if (!verified) {
        throw new Error('비밀번호가 틀렸습니다.')
      }

      if (props.embedded) {
        try { emit('edit-post', id) } catch (e) {}
        return
      }

      router.push({
        name: 'PostEdit',
        params: {
          id,
        },
      })
    } catch (caughtError) {
      error.value = (caughtError as Error).message
    }
  } else {
    try {
      await deletePost(id, password)

      router.push({
        name: 'Home',
      })
    } catch (caughtError) {
      error.value = (caughtError as Error).message
    }
  }

  pendingAction = null
}
</script>

<style scoped>
.post-detail-page {
  width: min(820px, 100%);
  margin: 0 auto;
}

.post-loading {
  min-height: 360px;

  display: grid;
  place-content: center;
  justify-items: center;
  gap: 14px;

  color: #7f8795;
  font-size: 13px;
}

.post-article {
  overflow: hidden;
}

.article-header {
  padding: 42px 46px 28px;
}

.article-header h1 {
  margin: 11px 0 0;

  color: #202635;
  font-size: clamp(30px, 5vw, 46px);
  font-weight: 880;
  letter-spacing: -0.052em;
  line-height: 1.2;
}

.article-meta {
  margin-top: 18px;

  display: flex;
  flex-wrap: wrap;
  gap: 14px;

  color: #9299a7;
  font-size: 11px;
  font-weight: 650;
}

.article-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.article-image {
  width: calc(100% - 48px);
  max-height: 480px;
  margin: 0 24px;

  border-radius: 18px;

  object-fit: cover;
}

.article-body {
  min-height: 220px;
  padding: 34px 46px 46px;
}

.article-body p {
  margin: 0;

  color: #515b6d;
  font-size: 15px;
  line-height: 1.95;
  white-space: pre-wrap;
}

.article-footer {
  padding: 18px 24px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;

  border-top: 1px solid #eceef2;

  background: #fafafd;
}

.article-footer p {
  margin: 0;

  color: #9299a7;
  font-size: 10px;
  line-height: 1.5;
}

.article-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

@media (max-width: 640px) {
  .article-header {
    padding: 30px 22px 22px;
  }

  .article-image {
    width: calc(100% - 28px);
    margin-inline: 14px;

    border-radius: 14px;
  }

  .article-body {
    min-height: 180px;
    padding: 26px 22px 34px;
  }

  .article-footer {
    align-items: stretch;
    flex-direction: column;

    padding: 18px;
  }

  .article-actions .btn {
    flex: 1;
  }
}
</style>