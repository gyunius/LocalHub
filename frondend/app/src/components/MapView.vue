<template>
  <div ref="mapEl" class="w-full h-[70vh] rounded border"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getAllItems } from '../services/tourService';
import type { TourItem } from '../types/tour';

const props = defineProps<{ filename?: string }>();
const filename = props.filename ?? '서울_관광지.json';

const mapEl = ref<HTMLDivElement | null>(null);
let map: L.Map | null = null;
let markersLayer: L.LayerGroup | null = null;
const router = useRouter();

const DefaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function toNumber(v?: string) {
  if (!v) return NaN;
  const n = parseFloat(v.replace(/,/g, ''));
  return Number.isFinite(n) ? n : NaN;
}

onMounted(async () => {
  if (!mapEl.value) return;

  map = L.map(mapEl.value, { preferCanvas: true }).setView([37.5665, 126.9780], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);

  try {
    const items: TourItem[] = await getAllItems(filename);
    const bounds = L.latLngBounds([]);

    for (const it of items) {
      const lat = toNumber(it.mapy);
      const lng = toNumber(it.mapx);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;

      const marker = L.marker([lat, lng], { icon: DefaultIcon }).addTo(markersLayer);
      marker.bindTooltip(it.title || '', { direction: 'top', offset: [0, -10] });

      // popup with brief info (clicking marker navigates)
      marker.bindPopup(
        `<div style="min-width:140px"><strong>${(it.title||'')}</strong><div style="font-size:12px;color:#666">${it.addr1||''}</div><div style="margin-top:6px"><a href="/place/${it.contentid}">상세보기</a></div></div>`
      );

      marker.on('click', () => {
        router.push({ name: 'Place', params: { id: it.contentid } });
      });

      bounds.extend([lat, lng]);
    }

    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.1));
    }
  } catch (e) {
    // 실패해도 맵은 보이게 함
    // 확인용 콘솔 출력
    // eslint-disable-next-line no-console
    console.error('Map load error:', e);
  }
});

onBeforeUnmount(() => {
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<style scoped>
/* 필요시 마커 팝업 스타일 조정 */
</style>