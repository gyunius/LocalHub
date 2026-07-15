<template>
  <div class="map-shell">
    <div
      ref="mapEl"
      class="map-canvas"
      aria-label="서울 관광지 지도"
    ></div>

    <!-- 필터 오버레이: map-floating-info 위에 배치 -->
    <div class="absolute" style="left:14px; bottom:80px; z-index:800;">
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

      <div class="bg-white rounded px-3 py-1 text-sm border mt-2">
        {{ visibleCount }} / {{ totalCount }} 장소
      </div>
    </div>

    <div class="map-floating-info" aria-live="polite">
      <span class="map-pin-mini" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none">
          <path d="M12 21s7-5.07 7-12A7 7 0 1 0 5 9c0 6.93 7 12 7 12Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
          <circle cx="12" cy="9" r="2.2" fill="currentColor"/>
        </svg>
      </span>

      <span v-if="loading">관광지를 불러오는 중</span>
      <span v-else>{{ markerCount }}개의 장소</span>
    </div>

    <div v-if="loading" class="map-loading" role="status" aria-live="polite">
      <div class="map-loading-card">
        <div class="loading-ring" aria-hidden="true" />
        <div>
          <strong>지도를 준비하고 있어요</strong>
          <span>서울의 관광지를 지도에 표시하는 중입니다.</span>
        </div>
      </div>
    </div>

    <div v-if="error" class="map-error alert alert-error" role="alert">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
        <path d="M12 8v5m0 3.2v.1M10.3 4.5 3.4 17a2 2 0 0 0 1.75 3h13.7a2 2 0 0 0 1.75-3L13.7 4.5a2 2 0 0 0-3.4 0Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import { getAllItems } from '../services/tourService'
import type { TourItem } from '../types/tour'
import { selectedDistrict, setSelectedDistrict } from '../stores/filterStore'

const props = defineProps<{ filename?: string }>();
const filename = props.filename ?? '서울_관광지.json'

const mapEl = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref('')
const allItems = ref<TourItem[]>([])
const filterOpen = ref(false)

let map: L.Map | null = null
let markersLayer: L.LayerGroup | null = null

const router = useRouter()

const markerIcon = L.divIcon({
  className: 'localhub-marker-wrapper',
  html: `
    <span class="localhub-marker" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
        <path d="M12 21s7-5.07 7-12A7 7 0 1 0 5 9c0 6.93 7 12 7 12Z" fill="currentColor"/>
        <circle cx="12" cy="9" r="2.7" fill="white"/>
      </svg>
    </span>
  `,
  iconSize: [38, 44],
  iconAnchor: [19, 40],
  tooltipAnchor: [0, -34],
})

function toNumber(value?: string) {
  if (!value) return Number.NaN
  const parsed = Number.parseFloat(value.replace(/,/g, ''))
  return Number.isFinite(parsed) ? parsed : Number.NaN
}

function escapeHtml(value: string) {
  const replacements: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }
  return value.replace(/[&<>'"]/g, (ch) => replacements[ch] ?? ch)
}

function extractGu(addr?: string) {
  if (!addr) return null
  const m = addr.match(/([가-힣]+구)/)
  return m ? m[1] : null
}

const districts = computed(() => {
  const s = new Set<string>()
  for (const it of allItems.value) {
    const g = extractGu(it.addr1) || '기타'
    s.add(g)
  }
  const arr = Array.from(s).sort((a, b) => a.localeCompare(b, 'ko'))
  return ['전체', ...arr]
})

const visibleItems = computed(() => {
  const sel = selectedDistrict.value
  if (!sel || sel === '전체') return allItems.value
  return allItems.value.filter(it => (extractGu(it.addr1) || '기타') === sel)
})

const visibleCount = computed(() => visibleItems.value.length)
const totalCount = computed(() => allItems.value.length)
const selectedDistrictLabel = computed(() => selectedDistrict.value || '전체')
const markerCount = computed(() => visibleCount.value)

function selectDistrict(d: string) {
  setSelectedDistrict(d)
  filterOpen.value = false
}

function clearMarkers() {
  if (markersLayer) markersLayer.clearLayers()
}

function updateMarkers() {
  if (!map || !markersLayer) return
  clearMarkers()
  const bounds = L.latLngBounds([])

  for (const item of visibleItems.value) {
    const lat = toNumber(item.mapy)
    const lng = toNumber(item.mapx)
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue

    const marker = L.marker([lat, lng], { icon: markerIcon, keyboard: true, title: item.title || '관광지' })
      .addTo(markersLayer)

    marker.bindTooltip(
      `
        <div class="localhub-tooltip-title">${escapeHtml(item.title || '관광지')}</div>
        <div class="localhub-tooltip-address">${escapeHtml(item.addr1 || '주소 정보 없음')}</div>
      `,
      { direction: 'top', offset: [0, -9], opacity: 1 },
    )

    marker.on('click', () => {
      router.push({ name: 'Place', params: { id: item.contentid } })
    })

    bounds.extend([lat, lng])
  }

  // fit to visible markers
  if (bounds.isValid()) {
    map.fitBounds(bounds.pad(0.08), { maxZoom: 13 })
  }
}

watch([selectedDistrict, allItems], () => {
  updateMarkers()
})

onMounted(async () => {
  if (!mapEl.value) return

  map = L.map(mapEl.value, { preferCanvas: true, zoomControl: false, attributionControl: true }).setView([37.5665, 126.978], 11)

  L.control.zoom({ position: 'topright' }).addTo(map)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)

  try {
    const items: TourItem[] = await getAllItems(filename)
    allItems.value = items
    updateMarkers()
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Map load error:', err)
    error.value = '관광지 데이터를 불러오지 못했습니다.'
  } finally {
    loading.value = false
    window.setTimeout(() => map?.invalidateSize(), 50)
  }
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
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
  transition: transform 140ms ease, box-shadow 140ms ease;
}

:deep(.localhub-marker svg) {
  transform: rotate(45deg);
}

:deep(.localhub-marker-wrapper:hover .localhub-marker) {
  transform: rotate(-45deg) translate(2px, -2px) scale(1.07);
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
  .map-shell, .map-canvas { min-height: 520px; }
}

@media (max-width: 640px) {
  .map-shell, .map-canvas { min-height: 440px; }
}
</style>