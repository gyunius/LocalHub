<template>
  <transition name="modal">
    <div
      v-if="show"
      class="modal"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      @keydown.esc="close"
    >
      <div
        class="modal-backdrop"
        @click="close"
      ></div>

      <form
        class="modal-panel"
        @submit.prevent="confirm"
      >
        <div class="modal-heading">
          <div
            class="modal-icon"
            aria-hidden="true"
          >
            <svg
              viewBox="0 0 24 24"
              width="21"
              height="21"
              fill="none"
            >
              <rect
                x="5"
                y="10"
                width="14"
                height="10"
                rx="2"
                stroke="currentColor"
                stroke-width="1.8"
              />

              <path
                d="M8.5 10V7.5a3.5 3.5 0 1 1 7 0V10M12 14v2.5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
              />
            </svg>
          </div>

          <div>
            <h3 :id="titleId">
              {{ title || '비밀번호 확인' }}
            </h3>

            <p>
              게시글 작성 시 설정한 비밀번호를 입력해주세요.
            </p>
          </div>

          <button
            type="button"
            class="modal-close"
            aria-label="닫기"
            @click="close"
          >
            <svg
              viewBox="0 0 24 24"
              width="18"
              height="18"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="m7 7 10 10M17 7 7 17"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
              />
            </svg>
          </button>
        </div>

        <label class="form-field modal-field">
          <span class="form-label">
            비밀번호
          </span>

          <input
            ref="passwordInput"
            v-model="password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            class="form-input"
            autocomplete="current-password"
          />
        </label>

        <div class="modal-actions">
          <button
            type="button"
            class="btn btn-secondary"
            @click="close"
          >
            취소
          </button>

          <button
            type="submit"
            class="btn btn-primary"
            :disabled="!password"
          >
            확인
          </button>
        </div>
      </form>
    </div>
  </transition>
</template>

<script setup lang="ts">
import {
  nextTick,
  ref,
  watch,
} from 'vue'

const props = defineProps<{
  show: boolean
  title?: string
}>()

const emit = defineEmits<{
  confirm: [password: string]
  close: []
  'update:show': [value: boolean]
}>()

const password = ref('')
const passwordInput =
  ref<HTMLInputElement | null>(null)

const titleId =
  `password-modal-${Math.random()
    .toString(36)
    .slice(2)}`

watch(
  () => props.show,
  async (visible) => {
    if (!visible) {
      password.value = ''
      return
    }

    await nextTick()

    passwordInput.value?.focus()
  },
)

function confirm() {
  if (!password.value) {
    return
  }

  emit('confirm', password.value)
  emit('update:show', false)

  password.value = ''
}

function close() {
  emit('close')
  emit('update:show', false)

  password.value = ''
}
</script>

<style scoped>
.modal-heading {
  display: grid;
  grid-template-columns:
    auto
    minmax(0, 1fr)
    auto;
  align-items: start;
  gap: 12px;
}

.modal-icon {
  width: 43px;
  height: 43px;

  display: grid;
  place-items: center;

  border-radius: 14px;

  color: #7543c7;
  background: #f1ebfa;
}

.modal-heading h3 {
  margin: 1px 0 0;

  color: #20283a;
  font-size: 17px;
  font-weight: 850;
  letter-spacing: -0.025em;
}

.modal-heading p {
  margin: 5px 0 0;

  color: #8a92a3;
  font-size: 11px;
  line-height: 1.5;
}

.modal-close {
  width: 34px;
  height: 34px;

  display: grid;
  place-items: center;

  border-radius: 11px;

  color: #8d94a2;
  background: transparent;

  cursor: pointer;
}

.modal-close:hover {
  color: #4c5568;
  background: #f5f6f8;
}

.modal-field {
  margin-top: 22px;
}

.modal-actions {
  margin-top: 20px;

  display: flex;
  justify-content: flex-end;
  gap: 9px;
}

@media (max-width: 480px) {
  .modal-panel {
    padding: 20px;
  }

  .modal-actions .btn {
    flex: 1;
  }
}
</style>