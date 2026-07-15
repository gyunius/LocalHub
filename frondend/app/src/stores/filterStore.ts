import { ref } from 'vue';

// 기본값: '전체' (모든 구)
export const selectedDistrict = ref<string>('전체');

export function setSelectedDistrict(v: string) {
  selectedDistrict.value = v;
}