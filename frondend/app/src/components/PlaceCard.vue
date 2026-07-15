<template>
  <router-link
    :to="`/place/${item.contentid}`"
    class="place-card"
  >
    <div class="place-image-wrap">
      <img
        v-if="item.firstimage"
        :src="item.firstimage"
        :alt="item.title"
        class="place-image"
        loading="lazy"
      />

      <div
        v-else
        class="place-image-placeholder"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 24 24"
          width="24"
          height="24"
          fill="none"
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
            fill="currentColor"
          />
        </svg>
      </div>
    </div>

    <div class="place-copy">
      <span class="place-type">서울 관광지</span>

      <strong>{{ item.title }}</strong>

      <span class="place-address">
        <svg
          viewBox="0 0 24 24"
          width="14"
          height="14"
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

        {{ item.addr1 || '주소 정보 없음' }}
      </span>
    </div>

    <span class="place-arrow" aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        width="17"
        height="17"
        fill="none"
      >
        <path
          d="m9 5 7 7-7 7"
          stroke="currentColor"
          stroke-width="1.9"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </span>
  </router-link>
</template>

<script setup lang="ts">
import type { TourItem } from '../types/tour'

defineProps<{
  item: TourItem
}>()
</script>

<style scoped>
.place-card {
  padding: 12px;

  display: flex;
  align-items: center;
  gap: 13px;

  border: 1px solid #e8eaf0;
  border-radius: 17px;

  background: #ffffff;

  transition:
    transform 160ms ease,
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.place-card:hover {
  transform: translateY(-2px);

  border-color: #ddd4ef;

  box-shadow: 0 10px 26px rgba(46, 31, 76, 0.08);
}

.place-image-wrap {
  width: 88px;
  height: 70px;
  flex: 0 0 auto;
  overflow: hidden;

  border-radius: 13px;

  background: #eeeaf5;
}

.place-image {
  width: 100%;
  height: 100%;

  object-fit: cover;

  transition: transform 260ms ease;
}

.place-card:hover .place-image {
  transform: scale(1.04);
}

.place-image-placeholder {
  width: 100%;
  height: 100%;

  display: grid;
  place-items: center;

  color: #8b63c5;

  background: linear-gradient(
    145deg,
    #f3effa,
    #e8e1f5
  );
}

.place-copy {
  min-width: 0;
  flex: 1;

  display: grid;
  gap: 4px;
}

.place-type {
  color: #8052c1;
  font-size: 9px;
  font-weight: 850;
  letter-spacing: 0.04em;
}

.place-copy strong {
  overflow: hidden;

  color: #272d3c;
  font-size: 13px;
  font-weight: 820;
  letter-spacing: -0.02em;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.place-address {
  min-width: 0;
  overflow: hidden;

  display: flex;
  align-items: center;
  gap: 4px;

  color: #8a92a3;
  font-size: 10px;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.place-address svg {
  flex: 0 0 auto;
}

.place-arrow {
  width: 30px;
  height: 30px;
  flex: 0 0 auto;

  display: grid;
  place-items: center;

  border-radius: 10px;

  color: #9b91aa;
  background: #f7f6f9;

  transition:
    color 150ms ease,
    background 150ms ease,
    transform 150ms ease;
}

.place-card:hover .place-arrow {
  color: #6d3bae;
  background: #f0ebf8;

  transform: translateX(2px);
}
</style>