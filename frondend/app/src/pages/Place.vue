<template>
  <div>
    <button @click="$router.back()" class="mb-3 text-sm">← 뒤로</button>

    <div v-if="loading">로딩중...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <article v-else-if="item">
      <h2 class="text-2xl font-bold mb-2">{{ item.title }}</h2>
      <img v-if="item.firstimage" :src="item.firstimage" alt="" class="w-full max-w-xl rounded mb-4" />
      <p><strong>주소:</strong> {{ item.addr1 }} {{ item.addr2 }}</p>
      <p><strong>전화:</strong> {{ item.tel || '없음' }}</p>
      <p><strong>좌표:</strong> {{ item.mapy }}, {{ item.mapx }}</p>
    </article>

    <div v-else>데이터가 없습니다.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import type { TourItem } from '../types/tour';
import { getItemById } from '../services/tourService';

const route = useRoute();
const id = String(route.params.id || '');
const filename = '서울_관광지.json';

const item = ref<TourItem | null>(null);
const loading = ref(true);
const error = ref('');

onMounted(async () => {
  if (!id) {
    error.value = '잘못된 ID';
    loading.value = false;
    return;
  }
  try {
    const found = await getItemById(filename, id);
    if (!found) error.value = '항목을 찾을 수 없습니다.';
    else item.value = found;
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
});
</script>