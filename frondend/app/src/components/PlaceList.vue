<template>
  <div>
    <div class="mb-2 flex justify-between items-center">
      <h3 class="text-sm font-medium text-gray-700">관광지 목록</h3>
      <div class="text-xs text-gray-500">{{ visibleCount }} / {{ totalCount }}</div>
    </div>

    <div ref="scroller" class="h-[70vh] overflow-auto pr-2" @scroll="onScroll">
      <ul class="grid grid-cols-1 gap-3">
        <li v-for="it in visibleItems" :key="it.contentid">
          <PlaceCard :item="it" />
        </li>
      </ul>

      <div ref="sentinel" class="py-4 text-center text-sm text-gray-500" v-if="!allLoaded && !loading">
        스크롤하여 더 불러오기...
      </div>
      <div class="py-4 text-center text-sm text-gray-500" v-else-if="loading">
        로딩 중...
      </div>
      <div class="py-4 text-center text-sm text-gray-500" v-else>
        끝
      </div>
    </div>

    <div v-if="error" class="mt-2 text-red-600 text-sm">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import type { TourItem } from '../types/tour';
import { getAllItems } from '../services/tourService';
import PlaceCard from './PlaceCard.vue';

const props = defineProps<{ filename?: string; pageSize?: number }>();
const filename = props.filename ?? '서울_관광지.json';
const pageSize = props.pageSize ?? 20;

const allItems = ref<TourItem[]>([]);
const page = ref(1);
const loading = ref(false);
const error = ref('');
const scroller = ref<HTMLElement | null>(null);
const sentinel = ref<HTMLElement | null>(null);

const visibleItems = computed(() => allItems.value.slice(0, page.value * pageSize));
const visibleCount = computed(() => visibleItems.value.length);
const totalCount = computed(() => allItems.value.length);
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
  // fallback: when using scroll container
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