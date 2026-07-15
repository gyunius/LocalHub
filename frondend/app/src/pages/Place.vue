<template>
  <div class="detail-page">
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

      지도로 돌아가기
    </button>

    <div
      v-if="loading"
      class="surface-card detail-loading"
    >
      <div class="loading-ring"></div>
      <p>장소 정보를 불러오는 중이에요.</p>
    </div>

    <div
      v-else-if="error"
      class="alert alert-error detail-alert"
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
      v-else-if="item"
      class="place-detail surface-card"
    >
      <div class="place-visual">
        <img
          v-if="item.firstimage"
          :src="item.firstimage"
          :alt="item.title"
        />

        <div
          v-else
          class="visual-placeholder"
          aria-hidden="true"
        >
          <div class="placeholder-mark">
            <svg
              viewBox="0 0 24 24"
              width="38"
              height="38"
              fill="none"
            >
              <path
                d="M12 21s7-5.07 7-12A7 7 0 1 0 5 9c0 6.93 7 12 7 12Z"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linejoin="round"
              />

              <circle
                cx="12"
                cy="9"
                r="2.3"
                fill="currentColor"
              />
            </svg>
          </div>
        </div>

        <span class="visual-badge">
          서울 관광지
        </span>
      </div>

      <div class="place-content">
        <div class="eyebrow">Local place</div>

        <h1>{{ item.title }}</h1>

        <p class="place-summary">
          서울에서 새롭게 발견할 수 있는 장소입니다.
          방문 전 주소와 연락처를 확인해주세요.
        </p>

        <div class="info-grid">
          <div class="info-card">
            <span class="info-icon">
              <svg
                viewBox="0 0 24 24"
                width="20"
                height="20"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M12 21s7-5.07 7-12A7 7 0 1 0 5 9c0 6.93 7 12 7 12Z"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linejoin="round"
                />

                <circle
                  cx="12"
                  cy="9"
                  r="2.2"
                  stroke="currentColor"
                  stroke-width="1.7"
                />
              </svg>
            </span>

            <div>
              <span>주소</span>

              <strong>
                {{ fullAddress || '주소 정보 없음' }}
              </strong>
            </div>
          </div>

          <div class="info-card">
            <span class="info-icon">
              <svg
                viewBox="0 0 24 24"
                width="20"
                height="20"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M8.1 3.5h-3A1.6 1.6 0 0 0 3.5 5.1c0 8.5 6.9 15.4 15.4 15.4a1.6 1.6 0 0 0 1.6-1.6v-3l-4-1.3-1.1 2.2a13.1 13.1 0 0 1-8.2-8.2l2.2-1.1-1.3-4Z"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </span>

            <div>
              <span>전화</span>

              <a
                v-if="item.tel"
                :href="`tel:${item.tel}`"
              >
                {{ item.tel }}
              </a>

              <strong v-else>
                등록된 번호 없음
              </strong>
            </div>
          </div>

          <div class="info-card info-card-wide">
            <span class="info-icon">
              <svg
                viewBox="0 0 24 24"
                width="20"
                height="20"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M9 18 3.8 20.6A.55.55 0 0 1 3 20.1V6.8a1 1 0 0 1 .55-.9L9 3.2m0 14.8 6 3m-6-3V3.2m6 17.8 5.45-2.7a1 1 0 0 0 .55-.9V4.1a.55.55 0 0 0-.8-.5L15 6.2m0 14.8V6.2M9 3.2l6 3"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </span>

            <div>
              <span>지도 좌표</span>
              <strong>{{ coordinates }}</strong>
            </div>
          </div>
        </div>
      </div>
    </article>

    <div
      v-else
      class="empty-state surface-card"
    >
      데이터가 없습니다.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getItemById } from '../services/tourService'
import type { TourItem } from '../types/tour'

const route = useRoute()

const id = String(route.params.id || '')
const filename = '서울_관광지.json'

const item = ref<TourItem | null>(null)
const loading = ref(true)
const error = ref('')

const fullAddress = computed(() =>
  [
    item.value?.addr1,
    item.value?.addr2,
  ]
    .filter(Boolean)
    .join(' '),
)

const coordinates = computed(() => {
  if (!item.value?.mapy || !item.value?.mapx) {
    return '좌표 정보 없음'
  }

  return `${item.value.mapy}, ${item.value.mapx}`
})

onMounted(async () => {
  if (!id) {
    error.value = '잘못된 장소 ID입니다.'
    loading.value = false
    return
  }

  try {
    const found = await getItemById(filename, id)

    if (!found) {
      error.value = '항목을 찾을 수 없습니다.'
    } else {
      item.value = found
    }
  } catch (caughtError) {
    console.error('Place detail load error:', caughtError)

    error.value =
      caughtError instanceof Error
        ? caughtError.message
        : '장소 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.detail-page {
  width: min(1120px, 100%);
  margin: 0 auto;
}

.detail-loading {
  min-height: 360px;

  display: grid;
  place-content: center;
  justify-items: center;
  gap: 14px;

  color: #7f8795;
  font-size: 13px;
}

.detail-alert {
  margin-top: 20px;
}

.place-detail {
  display: grid;
  grid-template-columns:
    minmax(0, 1.08fr)
    minmax(380px, 0.92fr);

  overflow: hidden;
}

.place-visual {
  position: relative;

  min-height: 560px;
  overflow: hidden;

  background: #eeeaf4;
}

.place-visual::after {
  content: "";

  position: absolute;
  inset: auto 0 0;

  height: 34%;

  pointer-events: none;

  background: linear-gradient(
    transparent,
    rgba(20, 14, 31, 0.28)
  );
}

.place-visual img {
  width: 100%;
  height: 100%;
  min-height: 560px;

  object-fit: cover;
}

.visual-placeholder {
  width: 100%;
  height: 100%;
  min-height: 560px;

  display: grid;
  place-items: center;

  color: #7543c7;

  background:
    radial-gradient(
      circle at 25% 20%,
      rgba(255, 255, 255, 0.72),
      transparent 24%
    ),
    linear-gradient(
      145deg,
      #f2eef9,
      #dcd2ee
    );
}

.placeholder-mark {
  width: 94px;
  height: 94px;

  display: grid;
  place-items: center;

  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 32px;

  background: rgba(255, 255, 255, 0.48);

  box-shadow:
    0 20px 54px rgba(64, 42, 100, 0.13);

  backdrop-filter: blur(12px);
}

.visual-badge {
  position: absolute;
  z-index: 2;
  left: 22px;
  bottom: 22px;

  min-height: 32px;
  padding: 0 12px;

  display: inline-flex;
  align-items: center;

  border: 1px solid rgba(255, 255, 255, 0.54);
  border-radius: 999px;

  color: #ffffff;
  background: rgba(28, 21, 40, 0.38);

  backdrop-filter: blur(10px);

  font-size: 11px;
  font-weight: 800;
}

.place-content {
  padding: 46px;

  display: flex;
  flex-direction: column;
  justify-content: center;
}

.place-content h1 {
  margin: 10px 0 0;

  color: #1e2433;
  font-size: clamp(30px, 4vw, 46px);
  font-weight: 880;
  letter-spacing: -0.055em;
  line-height: 1.12;
}

.place-summary {
  margin: 16px 0 0;

  color: #7a8292;
  font-size: 13px;
  line-height: 1.75;
}

.info-grid {
  margin-top: 30px;

  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.info-card {
  min-width: 0;
  padding: 14px;

  display: flex;
  align-items: flex-start;
  gap: 11px;

  border: 1px solid #e8eaf0;
  border-radius: 16px;

  background: #fafafd;
}

.info-card-wide {
  grid-column: 1 / -1;
}

.info-icon {
  width: 37px;
  height: 37px;
  flex: 0 0 auto;

  display: grid;
  place-items: center;

  border-radius: 12px;

  color: #7646bc;
  background: #eee8f8;
}

.info-card span,
.info-card strong,
.info-card a {
  display: block;
}

.info-card div > span {
  color: #9299a7;
  font-size: 10px;
  font-weight: 700;
}

.info-card strong,
.info-card a {
  margin-top: 4px;
  overflow-wrap: anywhere;

  color: #3d4556;
  font-size: 11px;
  font-weight: 760;
  line-height: 1.5;
}

.info-card a:hover {
  color: #6032ad;
}

@media (max-width: 900px) {
  .place-detail {
    grid-template-columns: 1fr;
  }

  .place-visual,
  .place-visual img,
  .visual-placeholder {
    min-height: 390px;
  }

  .place-content {
    padding: 32px;
  }
}

@media (max-width: 560px) {
  .place-visual,
  .place-visual img,
  .visual-placeholder {
    min-height: 300px;
  }

  .place-content {
    padding: 24px 20px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .info-card-wide {
    grid-column: auto;
  }
}
</style>