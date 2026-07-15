<template>
  <div class="place-list-wrap">
    <div class="place-list-meta">
      <span>관광지 목록</span>

      <span class="count-badge">
        {{ visibleCount }} / {{ totalCount }}
      </span>
    </div>

    <div
      ref="scroller"
      class="place-scroller pretty-scrollbar"
      @scroll="onScroll"
    >
      <div
        v-if="loading && !visibleItems.length"
        class="empty-state"
      >
        <div>
          <div class="loading-ring mx-auto"></div>
          <p class="mt-3">관광지를 불러오는 중이에요.</p>
        </div>
      </div>

      <ul v-else class="place-list">
        <li
          v-for="item in visibleItems"
          :key="item.contentid"
        >
          <PlaceCard :item="item" />
        </li>
      </ul>

      <div
        v-if="!allLoaded && !loading"
        ref="sentinel"
        class="list-status"
      >
        스크롤하면 더 많은 장소를 볼 수 있어요.
      </div>

      <div
        v-else-if="loading"
        class="list-status"
      >
        불러오는 중...
      </div>

      <div
        v-else-if="visibleItems.length"
        class="list-status"
      >
        모든 장소를 확인했어요.
      </div>
    </div>

    <div
      v-if="error"
      class="alert alert-error place-error"
    >
      {{ error }}
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import type { TourItem } from '../types/tour';
import { getAllItems } from '../services/tourService';
import PlaceCard from './PlaceCard.vue';
import { selectedDistrict } from '../stores/filterStore';

const props = defineProps<{ filename?: string; pageSize?: number }>();
const filename = props.filename ?? '서울_관광지.json';
const pageSize = props.pageSize ?? 20;

const allItems = ref<TourItem[]>([]);
const page = ref(1);
const loading = ref(false);
const error = ref('');
const scroller = ref<HTMLElement | null>(null);
const sentinel = ref<HTMLElement | null>(null);

function extractGu(addr?: string): string | null {
  if (!addr) return null;
  const m = addr.match(/([가-힣]+구)/);
  return m ? m[1] : null;
}

const filteredItems = computed(() => {
  const sel = selectedDistrict.value;
  return allItems.value.filter((it) => {
    if (!it) return false;
    const g = extractGu(it.addr1) || '기타';
    return sel === '전체' || sel === g;
  });
});

const visibleItems = computed(() => filteredItems.value.slice(0, page.value * pageSize));
const visibleCount = computed(() => visibleItems.value.length);
const totalCount = computed(() => filteredItems.value.length);
const allLoaded = computed(() => visibleCount.value >= totalCount.value);

let observer: IntersectionObserver | null = null;

async function loadAll() {
  loading.value = true;
  try {
    allItems.value = await getAllItems(filename);
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}

function loadMore() {
  if (allLoaded.value) return;
  page.value += 1;
}

function onScroll() {
  if (!scroller.value || allLoaded.value) return;
  const el = scroller.value;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) {
    loadMore();
  }
}

onMounted(async () => {
  await loadAll();

  if (sentinel.value) {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !loading.value && !allLoaded.value) {
            loadMore();
          }
        });
      },
      { root: scroller.value, threshold: 0.1 }
    );
    observer.observe(sentinel.value);
  }
});

onBeforeUnmount(() => {
  if (observer && sentinel.value) observer.unobserve(sentinel.value);
});
</script>

<style scoped>
.place-list-wrap {
  min-height: 0;
}

.place-list-meta {
  padding: 14px 20px 10px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  color: #8a92a3;
  font-size: 11px;
  font-weight: 700;
}

.place-scroller {
  max-height: 560px;
  padding: 4px 12px 12px;

  overflow-y: auto;
}

.place-list {
  margin: 0;
  padding: 0;

  display: grid;
  gap: 10px;

  list-style: none;
}

.list-status {
  padding: 18px 8px 8px;

  color: #a0a6b2;
  text-align: center;
  font-size: 10px;
  font-weight: 650;
}

.place-error {
  margin: 10px 12px 12px;
}
</style>