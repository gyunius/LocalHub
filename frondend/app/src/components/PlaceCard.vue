<template>
  <router-link :to="`/place/${item.contentid}`" class="flex gap-3 items-center p-3 border rounded hover:bg-gray-50">
    <img v-if="item.firstimage" :src="item.firstimage" class="w-24 h-16 object-cover rounded" alt="" />
    <div>
      <div class="font-medium">{{ item.title }}</div>
      <div class="text-sm text-gray-600">{{ item.addr1 }}</div>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import type { TourItem } from '../types/tour';
const props = defineProps<{ item: TourItem }>();
</script>