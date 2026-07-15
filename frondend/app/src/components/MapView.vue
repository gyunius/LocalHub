<template>
  <div class="map-shell">
    <div
      ref="mapEl"
      class="map-canvas"
      aria-label="서울 관광지 지도"
    ></div>

    <!-- 필터 오버레이: 체크박스 + 검색 -->
    <div class="absolute" style="left:14px; bottom:80px; z-index:800;">
      <div class="relative">
        <button @click="filterOpen = !filterOpen" class="bg-white text-sm px-3 py-1 rounded border">
          {{ selectedDistrictLabel }}
        </button>

        <div v-if="filterOpen" class="absolute left-0 bottom-12 bg-white border rounded p-3 max-h-64 overflow-auto w-72 filter-panel" role="dialog" aria-label="구 필터">
          <input
            v-model="searchQuery"
            type="search"
            class="filter-search"
            placeholder="구 이름으로 검색하세요"
            aria-label="구 검색"
          />

          <div role="group" aria-label="구 선택" class="mt-2">
            <label
              v-for="d in filteredDistricts"
              :key="d"
              class="radio-item"
              :aria-checked="isChecked(d)"
              tabindex="0"
              @keydown.enter.prevent="toggleDistrict(d)"
            >
              <input
                type="checkbox"
                :checked="isChecked(d)"
                @change="toggleDistrict(d)"
                class="radio-input"
                :aria-label="d"
              />
              <span class="text-sm truncate">{{ d }}</span>
            </label>
          </div>
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

    <!-- 장소 인포 패널 -->
    <div
      v-if="activeItem"
      class="map-info-panel surface-card"
      role="dialog"
      aria-label="장소 정보"
    >
      <button type="button" class="map-info-close" @click="activeItem = null" aria-label="정보 닫기">×</button>

      <h3 class="map-info-title">{{ activeItem.title }}</h3>

      <div class="map-info-media">
        <img
          v-if="activeItem.firstimage"
          :src="activeItem.firstimage"
          :alt="activeItem.title"
          class="map-info-image"
        />
        <div v-else class="map-info-image placeholder" aria-hidden="true">이미지 없음</div>
      </div>

      <p class="map-info-desc">
        {{ activeItem.overview || '서울에서 새롭게 발견할 수 있는 장소입니다. 방문 전 주소와 연락처를 확인해주세요.' }}
      </p>

      <div class="map-info-meta">
        <div><strong>주소</strong>
          <div class="muted">{{ [activeItem.addr1, activeItem.addr2].filter(Boolean).join(' ') || '주소 정보 없음' }}</div>
        </div>

        <div style="margin-top:8px"><strong>전화</strong>
          <div v-if="activeItem.tel"><a :href="`tel:${activeItem.tel}`">{{ activeItem.tel }}</a></div>
          <div v-else>등록된 번호 없음</div>
        </div>
      </div>

      <div class="map-info-actions" style="margin-top:10px">
        <button type="button" class="btn-sm" @click="activeItem = null">닫기</button>
        <button
          v-if="activeItem"
          type="button"
          class="btn-sm"
          style="margin-left:8px"
          @click="goToPlace(activeItem.contentid)"
        >
          자세히 보기
        </button>
      </div>
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
import 'leaflet.markercluster/dist/leaflet.markercluster.js'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

import { getAllItems } from '../services/tourService'
import type { TourItem } from '../types/tour'
import { selectedDistricts, setSelectedDistricts } from '../stores/filterStore'

const props = defineProps<{ filename?: string; routeMode?: boolean }>()
const emit = defineEmits<{
  (e: 'route-changed', route: Array<{ contentid: string | number; title?: string; lat?: number; lng?: number; order: number }>): void
}>()

const filename = props.filename ?? '서울_관광지.json'

const mapEl = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref('')
const allItems = ref<TourItem[]>([])
const filterOpen = ref(false)
const searchQuery = ref('')
const activeItem = ref<TourItem | null>(null)

let map: L.Map | null = null
let markersLayer: any = null
let smallMarkersLayer: any = null
let initialFitDone = false

const router = useRouter()

let fetchTimer: number | null = null
const DEBOUNCE_MS = 300
const CLUSTER_MIN_SIZE = 6
const CLUSTER_RADIUS_PX = 60

const STORAGE_KEY = 'localhub.mapview'

function saveMapView() {
  if (!map) return
  try {
    const c = map.getCenter()
    const z = map.getZoom()
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ lat: c.lat, lng: c.lng, zoom: z, ts: Date.now() }))
  } catch (e) {}
}

function goToPlace(id: string | number) {
  saveMapView()
  sessionStorage.setItem('localhub.restoreOnReturn', '1')
  router.push({ name: 'Place', params: { id } })
}

async function fetchPoisForBounds(bounds: L.LatLngBounds) {
  const pad = 0.06
  const sw = bounds.getSouthWest()
  const ne = bounds.getNorthEast()
  const minLat = sw.lat - (ne.lat - sw.lat) * pad
  const minLng = sw.lng - (ne.lng - sw.lng) * pad
  const maxLat = ne.lat + (ne.lat - sw.lat) * pad
  const maxLng = ne.lng + (ne.lng - sw.lng) * pad

  const bbox = [minLng, minLat, maxLng, maxLat].map((v) => v.toFixed(6)).join(',')

  try {
    const res = await fetch(`/api/pois?bbox=${encodeURIComponent(bbox)}&limit=10000`)
    if (res.ok) {
      const json = await res.json()
      const items = json.items || []
      allItems.value = items
      return
    }
  } catch (e) {}

  try {
    const data = await getAllItems(filename)
    allItems.value = data
  } catch (e) {
    error.value = '관광지 데이터를 불러오지 못했습니다.'
  }
}

function toNumber(value?: string | number) {
  if (value === undefined || value === null) return Number.NaN
  if (typeof value === 'number') return Number.isFinite(value) ? value : Number.NaN
  const s = String(value).trim()
  if (!s) return Number.NaN
  const parsed = Number.parseFloat(s.replace(/,/g, ''))
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

const filteredDistricts = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return districts.value
  return districts.value.filter(d => d === '전체' || d.toLowerCase().includes(q))
})

const visibleItems = computed(() => {
  const sel = selectedDistricts.value
  if (!sel.length) return []
  return allItems.value.filter(it => {
    if (!it) return false
    const g = extractGu(it.addr1) || '기타'
    return sel.includes(g)
  })
})

const visibleCount = computed(() => visibleItems.value.length)
const totalCount = computed(() => allItems.value.length)

const selectedDistrictLabel = computed(() => {
  const sel = selectedDistricts.value
  const all = districts.value.filter(d => d !== '전체')
  if (sel.length === 0) return '선택 없음'
  if (sel.length === all.length) return '전체'
  if (sel.length === 1) return sel[0]
  return `${sel.length}개 선택`
})

const markerCount = computed(() => visibleCount.value)

// route list 저장 (JSON으로 내보낼 수 있는 형태)
const routeList = ref<Array<{ contentid: string | number; title?: string; lat?: number; lng?: number; order: number }>>([])

// 동적으로 아이콘 생성: order 있으면 번호 표시, selected이면 색상 토글, hideCenterDot이면 내부 흰 점 제거
function buildMarkerIcon(order?: number, selected = false, hideSvg = false) {
  const numberHtml = typeof order === 'number' ? `<span class="marker-order" aria-hidden="true">${order}</span>` : ''
  const selectedClass = selected ? ' selected' : ''
  const svgHtml = hideSvg ? '' : `
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" focusable="false" aria-hidden="true">
      <path d="M12 21s7-5.07 7-12A7 7 0 1 0 5 9c0 6.93 7 12 7 12Z" fill="currentColor"/>
      <circle cx="12" cy="9" r="2.7" fill="white"/>
    </svg>
  `
  return L.divIcon({
    className: 'localhub-marker-wrapper',
    html: `
      <span class="localhub-marker${selectedClass}" aria-hidden="true">
        ${svgHtml}
        ${numberHtml}
      </span>
    `,
    iconSize: [38, 44],
    iconAnchor: [19, 40],
    tooltipAnchor: [0, -34],
  })
}

function handleRouteMarkerClick(item: TourItem, marker: L.Marker) {
  const id = item.contentid
  if (routeList.value.find(r => String(r.contentid) === String(id))) return
  const lat = toNumber(item.mapy)
  const lng = toNumber(item.mapx)
  const order = routeList.value.length + 1
  routeList.value.push({ contentid: id, title: item.title, lat, lng, order })
  // 즉시 아이콘 업데이트
  marker.setIcon(buildMarkerIcon(order, true, !!props.routeMode))
  emit('route-changed', routeList.value.slice())
}

function clearMarkers() {
  if (markersLayer && markersLayer.clearLayers) markersLayer.clearLayers()
  if (smallMarkersLayer && smallMarkersLayer.clearLayers) smallMarkersLayer.clearLayers()
}

function updateMarkers() {
  if (!map || !markersLayer) return
  clearMarkers()
  const bounds = L.latLngBounds([])

  const entries: Array<{ item: TourItem; lat: number; lng: number; marker: L.Marker; point?: L.Point }> = []
  for (const item of visibleItems.value) {
    const lat = toNumber(item.mapy)
    const lng = toNumber(item.mapx)
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue

    const selectedIndex = routeList.value.findIndex(r => String(r.contentid) === String(item.contentid))
    const isSelected = selectedIndex >= 0
    const order = isSelected ? routeList.value[selectedIndex].order : undefined
    const icon = buildMarkerIcon(order, isSelected, !!props.routeMode)

    const marker = L.marker([lat, lng], { icon, keyboard: true, title: item.title || '관광지' })

    marker.bindTooltip(
      `<div class="localhub-tooltip-title">${escapeHtml(item.title || '관광지')}</div>`,
      { direction: 'top', offset: [0, -9], opacity: 1 },
    )

    marker.on('click', () => {
      if (props.routeMode) {
        handleRouteMarkerClick(item, marker)
      } else {
        activeItem.value = item
        if (map) {
          try {
            map.setView([lat, lng], Math.max(map.getZoom(), 13), { animate: true })
          } catch (e) { /* ignore */ }
        }
      }
    })

    entries.push({ item, lat, lng, marker })
    bounds.extend([lat, lng])
  }

  if (!bounds.isValid()) return

  for (const e of entries) {
    e.point = map.latLngToLayerPoint(L.latLng(e.lat, e.lng))
  }

  const threshold = CLUSTER_RADIUS_PX
  const n = entries.length
  const adj: number[][] = Array.from({ length: n }, () => [])
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = entries[i].point!.x - entries[j].point!.x
      const dy = entries[i].point!.y - entries[j].point!.y
      if (dx * dx + dy * dy <= threshold * threshold) {
        adj[i].push(j)
        adj[j].push(i)
      }
    }
  }

  const visited = new Array(n).fill(false)
  for (let i = 0; i < n; i++) {
    if (visited[i]) continue
    const stack = [i]
    visited[i] = true
    const comp: number[] = []
    while (stack.length) {
      const cur = stack.pop()!
      comp.push(cur)
      for (const nb of adj[cur]) {
        if (!visited[nb]) { visited[nb] = true; stack.push(nb) }
      }
    }

    if (comp.length >= CLUSTER_MIN_SIZE) {
      for (const idx of comp) markersLayer.addLayer(entries[idx].marker)
    } else {
      for (const idx of comp) smallMarkersLayer.addLayer(entries[idx].marker)
    }
  }

  if (bounds.isValid()) {
    if (!initialFitDone) {
      map.fitBounds(bounds.pad(0.08), { maxZoom: 13 })
      initialFitDone = true
    }
  }
}

// watch: 마커/데이터/모드 변경 시 다시 그리기
watch([selectedDistricts, allItems, () => props.routeMode], () => {
  updateMarkers()
})

// routeMode가 켜질 때 새 경로 시작(원하면 비활성화로 변경 가능)
watch(() => props.routeMode, (val, oldVal) => {
  if (val && !oldVal) {
    // entering route mode: start fresh
    routeList.value = []
    emit('route-changed', routeList.value.slice())
  } else if (!val && oldVal) {
    // exiting route mode: clear selections and restore icons
    routeList.value = []
    activeItem.value = null
    emit('route-changed', routeList.value.slice())
  }
  updateMarkers()
})

// MapView.vue: 부모가 선택/카메라 상태를 가져갈 수 있도록 노출
defineExpose({
  exportSelection() {
    try { saveMapView() } catch (e) {}
    return {
      routeList: routeList.value.slice(),
      mapView: map ? { lat: map.getCenter().lat, lng: map.getCenter().lng, zoom: map.getZoom() } : null
    }
  }
})

onMounted(async () => {
  if (!mapEl.value) return

  map = L.map(mapEl.value, { preferCanvas: true, zoomControl: false, attributionControl: true }).setView([37.5665, 126.978], 11)
  const saved = sessionStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const s = JSON.parse(saved)
      if (s && Number.isFinite(s.lat) && Number.isFinite(s.lng) && Number.isFinite(s.zoom)) {
        map.setView([s.lat, s.lng], s.zoom)
        initialFitDone = true
      }
    } catch (e) {}
  }
  L.control.zoom({ position: 'topright' }).addTo(map)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)

  // @ts-ignore
  markersLayer = L.markerClusterGroup({ chunkedLoading: true, chunkProgress: (processed, total, node) => {} })
  markersLayer.addTo(map)
  smallMarkersLayer = L.layerGroup();
  smallMarkersLayer.addTo(map);

  map.on('moveend', onMapMove)
  map.on('zoomend', onMapMove)
  map.on('moveend', saveMapView)
  map.on('zoomend', saveMapView)
  map.on('click', () => { activeItem.value = null })

  try {
    const bounds = map.getBounds()
    await fetchPoisForBounds(bounds)

    if (!selectedDistricts.value.length) {
      const all = districts.value.filter(d => d !== '전체')
      setSelectedDistricts([...all])
    }

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
  saveMapView()
  map?.remove()
  map = null
})

function onMapMove() {
  if (!map) return
  if (fetchTimer) clearTimeout(fetchTimer)
  fetchTimer = window.setTimeout(() => {
    if (!map) return
    void fetchPoisForBounds(map.getBounds())
  }, DEBOUNCE_MS)
}
</script>

<style scoped>
/* 기존 스타일 유지 */
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

/* ... 나머지 스타일은 기존 파일과 동일합니다 (생략하지 마시고 이미 파일에 포함되어 있음) */
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

/* Filter panel styles */
.filter-panel {
  box-shadow: 0 12px 32px rgba(34, 27, 48, 0.08);
  background: #fff;
}

.filter-search {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid rgba(224, 220, 233, 0.95);
  border-radius: 8px;
  font-size: 13px;
  outline: none;
}

.filter-search:focus {
  box-shadow: 0 6px 18px rgba(114, 66, 189, 0.08);
  border-color: #7543c7;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  border-radius: 6px;
  cursor: pointer;
}

.radio-item:hover {
  background: #f7f5fb;
}

.radio-input {
  width: 16px;
  height: 16px;
  accent-color: #7543c7;
}

/* marker and tooltip styles (kept) */
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

:deep(.localhub-marker.selected) {
  background: linear-gradient(135deg, #7543c7, #6f49c8);
  color: #fff;
  box-shadow: 0 12px 28px rgba(96, 50, 173, 0.28);
  border: 3px solid rgba(255,255,255,0.96);
}

:deep(.localhub-marker .marker-order) {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 900;
  color: #fff;
  transform: rotate(45deg);
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

.map-info-panel {
  position: absolute;
  z-index: 850;
  right: 14px;
  bottom: 14px;
  width: 360px;
  max-width: calc(100% - 28px);
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 12px 36px rgba(20,16,40,0.12);
  background: #fff;
}

.map-info-close {
  position: absolute;
  right: 10px;
  top: 8px;
  border: none;
  background: transparent;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.map-info-title {
  font-size: 14px;
  font-weight: 800;
  margin: 6px 0 8px;
}

.map-info-image {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
}

.map-info-desc {
  margin: 8px 0;
  font-size: 13px;
  color: #6f7584;
}

.map-info-meta .muted {
  font-size: 13px;
  color: #485066;
  margin-top: 4px;
}

.btn-sm {
  padding: 6px 10px;
  font-size: 13px;
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.06);
  background: #fff;
  cursor: pointer;
}

@media (max-width: 960px) {
  .map-shell, .map-canvas { min-height: 520px; }
}

@media (max-width: 640px) {
  .map-shell, .map-canvas { min-height: 440px; }
}
</style>