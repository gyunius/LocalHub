<template>
  <div class="relative">
    <div ref="mapEl" class="w-full h-[70vh] rounded border"></div>

    <!-- 간결한 오버레이: 필터 버튼 + 장소 카운트 -->
    <div class="absolute left-4 bottom-4 flex flex-col items-start gap-2" style="z-index:800;">
      <div class="relative">
        <button @click="filterOpen = !filterOpen" class="bg-white text-sm px-3 py-1 rounded border">
          {{ selectedDistrictLabel }}
        </button>

        <div v-if="filterOpen" class="absolute left-0 bottom-12 bg-white border rounded p-2 max-h-56 overflow-auto w-44">
          <ul>
            <li v-for="d in districts" :key="d" class="mb-1">
              <button @click="selectDistrict(d)" class="w-full text-left text-sm px-2 py-1 hover:bg-gray-100 rounded">
                {{ d }}
              </button>
            </li>
          </ul>
        </div>
      </div>

      <div class="bg-white rounded px-3 py-1 text-sm border">
        {{ visibleCount }} / {{ totalCount }} 장소
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getAllItems } from '../services/tourService';
import type { TourItem } from '../types/tour';
import { selectedDistrict } from '../stores/filterStore';

const props = defineProps<{ filename?: string }>();
const filename = props.filename ?? '서울_관광지.json';

const mapEl = ref<HTMLDivElement | null>(null);
let map: L.Map | null = null;
let markersLayer: L.LayerGroup | null = null;
const router = useRouter();

const allItems = ref<TourItem[]>([]);
const filterOpen = ref(false);

function extractGu(addr?: string): string | null {
  if (!addr) return null;
  const m = addr.match(/([가-힣]+구)/);
  return m ? m[1] : null;
}

const districts = computed(() => {
  const s = new Set<string>();
  for (const it of allItems.value) {
    const g = extractGu(it.addr1) || '기타';
    s.add(g);
  }
  const arr = Array.from(s).sort((a, b) => a.localeCompare(b, 'ko'));
  return ['전체', ...arr];
});

const visibleItems = computed(() => {
  const sel = selectedDistrict.value;
  return allItems.value.filter((it) => {
    if (!it) return false;
    const g = extractGu(it.addr1) || '기타';
    return sel === '전체' || sel === g;
  });
});

const visibleCount = computed(() => visibleItems.value.length);
const totalCount = computed(() => allItems.value.length);

function toNumber(v?: string) {
  if (!v) return NaN;
  const n = parseFloat(v.replace(/,/g, ''));
  return Number.isFinite(n) ? n : NaN;
}

const DefaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function clearMarkers() {
  if (markersLayer) markersLayer.clearLayers();
}

function updateMarkers() {
  if (!map || !markersLayer) return;
  clearMarkers();
  const bounds = L.latLngBounds([]);
  for (const it of visibleItems.value) {
    const lat = toNumber(it.mapy);
    const lng = toNumber(it.mapx);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;

    const marker = L.marker([lat, lng], { icon: DefaultIcon }).addTo(markersLayer);
    marker.bindTooltip(it.title || '', { direction: 'top', offset: [0, -10] });
    marker.bindPopup(
      `<div style="min-width:140px"><strong>${(it.title || '')}</strong><div style="font-size:12px;color:#666">${it.addr1 || ''}</div><div style="margin-top:6px"><a href="/place/${it.contentid}">상세보기</a></div></div>`
    );
    marker.on('click', () => {
      router.push({ name: 'Place', params: { id: it.contentid } });
    });
    bounds.extend([lat, lng]);
  }
  if (bounds.isValid()) {
    map.fitBounds(bounds.pad(0.1));
  }
}

onMounted(async () => {
  if (!mapEl.value) return;

  map = L.map(mapEl.value, { preferCanvas: true }).setView([37.5665, 126.9780], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);

  try {
    allItems.value = await getAllItems(filename); // 기본: disabled 제외
    updateMarkers();
  } catch (e) {
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

watch([selectedDistrict, allItems], () => {
  updateMarkers();
});

function selectDistrict(d: string) {
  selectedDistrict.value = d;
  filterOpen.value = false;
}

const selectedDistrictLabel = computed(() => selectedDistrict.value || '전체');
</script>

<style scoped>
.map-shell {
  position: relative;

  min-height: 555px;
  overflow: hidden;

  border-radius: 18px;

  background: #e9e6f0;
}

.map-canvas {
  width: 100%;
  height: 100%;
  min-height: 555px;
}

.map-floating-info {
  position: absolute;
  z-index: 500;
  left: 14px;
  bottom: 14px;

  min-height: 38px;
  padding: 0 13px 0 9px;

  display: inline-flex;
  align-items: center;
  gap: 8px;

  border: 1px solid rgba(255, 255, 255, 0.78);
  border-radius: 999px;

  color: #4c435b;
  background: rgba(255, 255, 255, 0.9);

  box-shadow: 0 10px 28px rgba(34, 27, 48, 0.14);

  backdrop-filter: blur(12px);

  font-size: 11px;
  font-weight: 800;
}

.map-pin-mini {
  width: 25px;
  height: 25px;

  display: grid;
  place-items: center;

  border-radius: 999px;

  color: #7444bd;
  background: #f0eafb;
}

.map-loading {
  position: absolute;
  z-index: 600;
  inset: 0;

  padding: 24px;

  display: grid;
  place-items: center;

  pointer-events: none;

  background: rgba(244, 242, 248, 0.58);

  backdrop-filter: blur(3px);
}

.map-loading-card {
  padding: 15px 17px;

  display: flex;
  align-items: center;
  gap: 13px;

  border: 1px solid rgba(255, 255, 255, 0.85);
  border-radius: 17px;

  background: rgba(255, 255, 255, 0.94);

  box-shadow: 0 16px 42px rgba(43, 33, 62, 0.14);
}

.map-loading-card strong,
.map-loading-card span {
  display: block;
}

.map-loading-card strong {
  color: #2b3040;
  font-size: 12px;
  font-weight: 800;
}

.map-loading-card span {
  margin-top: 3px;

  color: #8c93a1;
  font-size: 10px;
}

.map-error {
  position: absolute;
  z-index: 650;
  right: 14px;
  bottom: 14px;

  max-width: calc(100% - 28px);

  box-shadow: 0 12px 32px rgba(83, 29, 36, 0.12);
}

:deep(.leaflet-control-zoom) {
  overflow: hidden;

  border: 0 !important;
  border-radius: 13px !important;

  box-shadow: 0 8px 24px rgba(43, 33, 62, 0.15) !important;
}

:deep(.leaflet-control-zoom a) {
  width: 38px !important;
  height: 38px !important;

  color: #51475f !important;

  border-color: #eeedf1 !important;

  background: rgba(255, 255, 255, 0.94) !important;

  font-size: 18px !important;
  line-height: 38px !important;
}

:deep(.leaflet-control-zoom a:hover) {
  color: #6032ad !important;
  background: #f7f4fd !important;
}

:deep(.leaflet-control-attribution) {
  border-radius: 8px 0 0 0;

  color: #7f8794;

  background: rgba(255, 255, 255, 0.78) !important;

  font-size: 8px;

  backdrop-filter: blur(5px);
}

:deep(.localhub-marker-wrapper) {
  border: 0;
  background: transparent;
}

:deep(.localhub-marker) {
  position: relative;

  width: 38px;
  height: 38px;

  display: grid;
  place-items: center;

  border: 3px solid rgba(255, 255, 255, 0.96);
  border-radius: 15px 15px 15px 5px;

  color: #7543c7;
  background: #ffffff;

  box-shadow: 0 8px 18px rgba(60, 36, 101, 0.28);

  transform: rotate(-45deg);

  transition:
    transform 140ms ease,
    box-shadow 140ms ease;
}

:deep(.localhub-marker svg) {
  transform: rotate(45deg);
}

:deep(.localhub-marker-wrapper:hover .localhub-marker) {
  transform:
    rotate(-45deg)
    translate(2px, -2px)
    scale(1.07);

  box-shadow: 0 12px 24px rgba(60, 36, 101, 0.36);
}

:deep(.leaflet-tooltip) {
  padding: 10px 12px;

  border: 1px solid rgba(224, 220, 233, 0.95);
  border-radius: 12px;

  color: #313747;
  background: rgba(255, 255, 255, 0.96);

  box-shadow: 0 12px 28px rgba(34, 27, 48, 0.16);

  backdrop-filter: blur(10px);
}

:deep(.leaflet-tooltip-top::before) {
  border-top-color: rgba(255, 255, 255, 0.96);
}

:deep(.localhub-tooltip-title) {
  max-width: 200px;
  overflow: hidden;

  font-size: 12px;
  font-weight: 850;

  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.localhub-tooltip-address) {
  max-width: 200px;
  margin-top: 3px;
  overflow: hidden;

  color: #8a92a3;
  font-size: 9px;

  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 960px) {
  .map-shell,
  .map-canvas {
    min-height: 520px;
  }
}

@media (max-width: 640px) {
  .map-shell,
  .map-canvas {
    min-height: 440px;
  }
}
</style>