<template>
  <div class="post-form-page">
    <button
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

      돌아가기
    </button>

    <form
      class="form-card surface-card"
      @submit.prevent="onSubmit"
    >
      <header class="form-header">
        <div
          class="form-header-icon"
          aria-hidden="true"
        >
          <svg
            viewBox="0 0 24 24"
            width="24"
            height="24"
            fill="none"
          >
            <path
              d="m14.5 5.5 4 4M4 20l4.1-.9L19 8.2a1.4 1.4 0 0 0 0-2l-1.2-1.2a1.4 1.4 0 0 0-2 0L4.9 15.9 4 20Z"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <div>
          <div class="eyebrow">
            Community story
          </div>

          <h1>
            {{
              isEdit
                ? '여행 이야기 수정'
                : '새 여행 이야기'
            }}
          </h1>

          <p>
            {{
              isEdit
                ? '기존 내용을 다듬어 다시 공유해보세요.'
                : '서울에서 발견한 장소와 유용한 팁을 다른 여행자에게 알려주세요.'
            }}
          </p>
        </div>
      </header>

      <div class="form-divider"></div>

      <div class="form-fields">
        <label class="form-field">
          <span class="form-label">
            제목

            <span class="form-hint">
              {{ form.title.length }}자
            </span>
          </span>

          <input
            v-model="form.title"
            class="form-input"
            maxlength="80"
            placeholder="예: 한강 벚꽃 산책 코스를 공유해요"
            autocomplete="off"
          />
        </label>

        <label class="form-field">
          <span class="form-label">
            내용

            <span class="form-hint">
              {{ form.content.length }}자
            </span>
          </span>

          <textarea
            v-model="form.content"
            class="form-input"
            maxlength="2000"
            placeholder="장소의 분위기, 추천 시간대, 이동 팁 등을 자유롭게 작성해주세요."
          ></textarea>
        </label>

        <label class="form-field">
          <span class="form-label">
            수정용 비밀번호

            <span class="form-hint">
              게시글에는 표시되지 않아요
            </span>
          </span>

          <div class="password-field">
            <svg
              viewBox="0 0 24 24"
              width="18"
              height="18"
              fill="none"
              aria-hidden="true"
            >
              <rect
                x="5"
                y="10"
                width="14"
                height="10"
                rx="2"
                stroke="currentColor"
                stroke-width="1.7"
              />

              <path
                d="M8.5 10V7.5a3.5 3.5 0 1 1 7 0V10"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
              />
            </svg>

            <input
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="수정·삭제 시 사용할 비밀번호"
              autocomplete="new-password"
            />
          </div>
        </label>

        <div
          v-if="error"
          class="alert alert-error"
        >
          <svg
            viewBox="0 0 24 24"
            width="18"
            height="18"
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
      </div>

      <footer class="form-actions">
        <button
          type="button"
          class="btn btn-secondary"
          :disabled="loading"
          @click="$router.back()"
        >
          취소
        </button>

        <button
          type="submit"
          class="btn btn-primary"
          :disabled="loading"
        >
          <span
            v-if="loading"
            class="submit-spinner"
          ></span>

          <svg
            v-else
            viewBox="0 0 24 24"
            width="17"
            height="17"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M5 12.5 9.2 17 19 7"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>

          {{
            loading
              ? '저장 중...'
              : isEdit
                ? '변경사항 저장'
                : '이야기 등록'
          }}
        </button>
      </footer>
    </form>
  </div>
</template>

<script setup lang="ts">
import {
  onMounted,
  reactive,
  ref,
} from 'vue'

import {
  useRoute,
  useRouter,
} from 'vue-router'

import {
  createPost,
  fetchPost,
  updatePost,
} from '../services/postService'

const route = useRoute()
const router = useRouter()

const id = String(route.params.id ?? '')
const isEdit = Boolean(id)

const form = reactive({
  title: '',
  content: '',
  password: '',
})

const loading = ref(false)
const error = ref('')

onMounted(async () => {
  if (!isEdit) {
    return
  }

  loading.value = true

  try {
    const post = await fetchPost(id)

    form.title = post.title
    form.content = post.content
  } catch (caughtError) {
    error.value = (caughtError as Error).message
  } finally {
    loading.value = false
  }
})

async function onSubmit() {
  error.value = ''

  if (
    !form.title.trim() ||
    !form.content.trim() ||
    !form.password
  ) {
    error.value =
      '제목, 내용, 비밀번호를 모두 입력해주세요.'

    return
  }

  loading.value = true

  try {
    if (isEdit) {
      await updatePost(id, {
        title: form.title.trim(),
        content: form.content.trim(),
        password: form.password,
      })

      router.push({
        name: 'PostDetail',
        params: {
          id,
        },
      })
    } else {
      const created = await createPost({
        title: form.title.trim(),
        content: form.content.trim(),
        password: form.password,
      })

      router.push({
        name: 'PostDetail',
        params: {
          id: (created as any).id,
        },
      })
    }
  } catch (caughtError) {
    error.value = (caughtError as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.post-form-page {
  width: min(820px, 100%);
  margin: 0 auto;
}

.form-header {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.form-header-icon {
  width: 50px;
  height: 50px;
  flex: 0 0 auto;

  display: grid;
  place-items: center;

  border-radius: 16px;

  color: #7543c7;

  background: linear-gradient(
    145deg,
    #f2ecfa,
    #e8def7
  );
}

.form-header h1 {
  margin: 7px 0 0;

  color: #202635;
  font-size: 27px;
  font-weight: 870;
  letter-spacing: -0.045em;
}

.form-header p {
  margin: 7px 0 0;

  color: #858d9c;
  font-size: 12px;
  line-height: 1.6;
}

.form-divider {
  height: 1px;
  margin: 24px 0;

  background: #eceef2;
}

.form-fields {
  display: grid;
  gap: 20px;
}

.password-field {
  position: relative;
}

.password-field > svg {
  position: absolute;
  z-index: 1;
  top: 50%;
  left: 14px;

  color: #9ba2af;

  transform: translateY(-50%);

  pointer-events: none;
}

.password-field .form-input {
  padding-left: 43px;
}

.form-actions {
  margin-top: 26px;
  padding-top: 20px;

  display: flex;
  justify-content: flex-end;
  gap: 9px;

  border-top: 1px solid #eceef2;
}

.submit-spinner {
  width: 15px;
  height: 15px;

  border: 2px solid rgba(255, 255, 255, 0.42);
  border-top-color: #ffffff;
  border-radius: 999px;

  animation: spin 650ms linear infinite;
}

@media (max-width: 560px) {
  .form-header-icon {
    width: 44px;
    height: 44px;

    border-radius: 14px;
  }

  .form-header h1 {
    font-size: 23px;
  }

  .form-actions .btn {
    flex: 1;
  }
}
</style>