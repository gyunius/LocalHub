import { ref } from 'vue';

// 선택된 구 목록. 빈 배열이면 '필터 미적용(전체 보기)'로 처리됩니다.
export const selectedDistricts = ref<string[]>([])

export function setSelectedDistricts(v: string[]) {
  selectedDistricts.value = v
}

export function toggleDistrict(d: string) {
  const idx = selectedDistricts.value.indexOf(d)
  if (idx >= 0) selectedDistricts.value.splice(idx, 1)
  else selectedDistricts.value.push(d)
}

export function clearSelectedDistricts() {
  selectedDistricts.value = []
}