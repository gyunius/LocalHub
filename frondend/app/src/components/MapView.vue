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

    <div class="map-autofit-control" style="position:absolute; right:14px; top:14px; z-index:900;">
      <button type="button" class="btn-sm" @click="toggleAutoFit" :title="autoFitEnabled ? '자동 맞춤 켜짐' : '자동 맞춤 끔'">
        {{ autoFitEnabled ? '자동 맞춤: 켜짐' : '자동 맞춤: 끔' }}
      </button>
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
        {{ getOverview(activeItem) }}
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

    <!-- 선택된 코스 요약 패널 (지도 오른쪽 아래) -->
    <div v-if="routeList.length && !props.routeMode" class="map-route-summary surface-card" role="region" aria-label="선택된 코스">
      <div class="preview-header" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
        <strong>현재 경로</strong>
        <div>
          <button type="button" class="btn-sm" @click="clearRoute">초기화</button>
        </div>
      </div>

      <ul class="preview-list" style="list-style:none;padding:0;margin:0;display:grid;gap:8px">
        <li v-for="r in routeList" :key="r.contentid" style="display:flex;align-items:center;gap:8px">
          <div style="width:28px;height:28px;border-radius:6px;display:grid;place-items:center;background:linear-gradient(135deg,#7543c7,#6f49c8);color:#fff;font-weight:800">
            {{ r.order }}
          </div>
          <div style="font-size:13px;color:#202635">{{ r.title }}</div>
        </li>
      </ul>
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

    <div v-if="routeMessage" class="map-route-msg surface-card" role="status" aria-live="polite">
      <div class="map-loading-card">
        <div>
          <strong>{{ routeMessage }}</strong>
        </div>
      </div>
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
import { selectedDistricts, setSelectedDistricts, toggleDistrict } from '../stores/filterStore'

const props = defineProps<{ filename?: string; routeMode?: boolean; editingRoute?: boolean }>()
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
let polylineLayer: any = null
const lastUserInteraction = ref<number>(0)
const autoFitEnabled = ref(true)
const programmaticMove = ref(false)
let programmaticTimer: number | null = null

function beginProgrammaticMove(timeout = 900) {
  programmaticMove.value = true
  if (programmaticTimer) window.clearTimeout(programmaticTimer)
  programmaticTimer = window.setTimeout(() => {
    programmaticMove.value = false
    programmaticTimer = null
  }, timeout)
}

const router = useRouter()

let fetchTimer: number | null = null
const DEBOUNCE_MS = 300
const CLUSTER_MIN_SIZE = 6
const CLUSTER_RADIUS_PX = 60

// fraction of viewport the route bbox should occupy when auto-fitting (e.g. 0.1 = 10%)
const FIT_TARGET_FRAC = 0.5

const STORAGE_KEY = 'localhub.mapview'

function saveMapView() {
  if (!map) return
  if (programmaticMove.value) return
  try {
    const c = map.getCenter()
    const z = map.getZoom()
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ lat: c.lat, lng: c.lng, zoom: z, ts: Date.now() }))
  } catch (e) {}
}

function persistMapView() {
  if (!map) return
  try {
    const c = map.getCenter()
    const z = map.getZoom()
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ lat: c.lat, lng: c.lng, zoom: z, ts: Date.now() }))
  } catch (e) {}
}

function computeDesiredZoomForTarget(bounds: L.LatLngBounds, targetFrac: number) {
  if (!map) return null
  try {
    const size = map.getSize()
    const vw = size.x
    const vh = size.y
    const nePt = map.latLngToContainerPoint(bounds.getNorthEast())
    const swPt = map.latLngToContainerPoint(bounds.getSouthWest())
    const bboxPxW = Math.abs(nePt.x - swPt.x)
    const bboxPxH = Math.abs(nePt.y - swPt.y)
    const widthRatio = bboxPxW / vw
    const heightRatio = bboxPxH / vh
    const useWidth = widthRatio >= heightRatio
    const viewportPx = useWidth ? vw : vh
    const bboxPx = useWidth ? bboxPxW : bboxPxH
    if (!bboxPx || !isFinite(bboxPx) || bboxPx <= 0) return null
    const desiredPx = Math.max(16, viewportPx * targetFrac)
    const scaleNeeded = desiredPx / bboxPx
    if (!isFinite(scaleNeeded) || scaleNeeded <= 0) return null
    const deltaZoom = Math.log2(scaleNeeded)
    let desiredZoom = (map.getZoom() || 11) + deltaZoom
    const maxZoomAllowed = typeof (map as any).getMaxZoom === 'function' ? (map as any).getMaxZoom() : 19
    const minZoomAllowed = typeof (map as any).getMinZoom === 'function' ? (map as any).getMinZoom() : 0
    desiredZoom = Math.min(Math.max(desiredZoom, minZoomAllowed), maxZoomAllowed)
    return desiredZoom
  } catch (e) {
    return null
  }
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

const markerCount = computed(() => (showOnlyRoute.value ? routeList.value.length : visibleCount.value))

function isChecked(d: string) {
  if (d === '전체') {
    const all = districts.value.filter(x => x !== '전체')
    return selectedDistricts.value.length === all.length
  }
  return selectedDistricts.value.includes(d)
}

function getOverview(it?: TourItem | null) {
  return (it as any)?.overview || '서울에서 새롭게 발견할 수 있는 장소입니다. 방문 전 주소와 연락처를 확인해주세요.'
}

function clearRoute() {
  routeList.value = []
  try { sessionStorage.removeItem('localhub.routeSelection') } catch (e) {}
  updateMarkers()
  emit('route-changed', routeList.value.slice())
}

// Load and show a post's saved route by contentid array. If empty or not found,
// show a small message overlay. This is intended to be called by the parent
// (via defineExpose) when a post is opened.
async function showRouteFromPost(ids: Array<string | number> | null | undefined) {
  try { sessionStorage.removeItem(STORAGE_KEY) } catch (e) {}
  showOnlyRoute.value = true
  routeMessage.value = ''
  routeList.value = []

  if (!ids || !Array.isArray(ids) || ids.length === 0) {
    routeMessage.value = '여행 경로가 지정되지 않았습니다.'
    updateMarkers()
    return
  }

  const fetched: Array<any> = []
  for (let i = 0; i < ids.length; i++) {
    const id = ids[i]
    try {
      const res = await fetch(`/api/pois/${encodeURIComponent(String(id))}`)
      if (!res.ok) continue
      const json = await res.json()
      const lat = toNumber(json.mapy)
      const lng = toNumber(json.mapx)
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue
      fetched.push({ contentid: id, title: json.title, lat, lng, order: i + 1 })
    } catch (e) {
      // ignore individual failures
    }
  }

  if (!fetched.length) {
    routeMessage.value = '여행 경로가 지정되지 않았습니다.'
    routeList.value = []
    try { map?.invalidateSize() } catch (e) {}
    // small delay to allow map to recalc before trying to render
    await new Promise((res) => setTimeout(res, 60))
    try {
      (map as any)?.dragging?.enable?.()
      (map as any)?.scrollWheelZoom?.enable?.()
      (map as any)?.doubleClickZoom?.enable?.()
      (map as any)?.boxZoom?.enable?.()
      (map as any)?.keyboard?.enable?.()
      (map as any)?.tap?.enable?.()
    } catch (e) {}
    updateMarkers()
    return
  }

  routeList.value = fetched
  routeMessage.value = ''
  try { map?.invalidateSize() } catch (e) {}
  // allow layout to settle so fitBounds works reliably
  await new Promise((res) => setTimeout(res, 60))
  try {
    (map as any)?.dragging?.enable?.()
    (map as any)?.scrollWheelZoom?.enable?.()
    (map as any)?.doubleClickZoom?.enable?.()
    (map as any)?.boxZoom?.enable?.()
    (map as any)?.keyboard?.enable?.()
    (map as any)?.tap?.enable?.()
  } catch (e) {}
  updateMarkers()

  // after markers/polylines are added, ensure the route bbox occupies at least 50% of viewport
  await new Promise((res) => setTimeout(res, 180))
  if (!map) return
  try {
    const bounds = L.latLngBounds(routeList.value.map(r => [Number(r.lat), Number(r.lng)]))
    if (!bounds.isValid()) return

    // measure pixel size of bounds inside the container
    const ne = map.latLngToContainerPoint(bounds.getNorthEast())
    const sw = map.latLngToContainerPoint(bounds.getSouthWest())
    const bboxPxW = Math.abs(ne.x - sw.x)
    const bboxPxH = Math.abs(ne.y - sw.y)
    const size = map.getSize()
    const vw = size.x
    const vh = size.y
    const widthRatio = bboxPxW / vw
    const heightRatio = bboxPxH / vh
    const maxRatio = Math.max(widthRatio, heightRatio)

    // fitting is handled centrally in updateMarkers() to avoid duplicate/conflicting setView calls
  } catch (e) {
    // ignore measurement errors
  }
}

// route list 저장 (JSON으로 내보낼 수 있는 형태)
const routeList = ref<Array<{ contentid: string | number; title?: string; lat?: number; lng?: number; order: number }>>([])
// when true, map will show only markers from `routeList` (used when displaying a post's saved route)
const showOnlyRoute = ref(false)
// message to show when route is empty or unavailable
const routeMessage = ref('')

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

function handleRouteMarkerClick(item: TourItem) {
  const id = item.contentid
  const idx = routeList.value.findIndex(r => String(r.contentid) === String(id))

  // 이미 선택된 항목이면 제거 (토글)
  if (idx >= 0) {
    routeList.value.splice(idx, 1)
    // 이후 항목들의 순서를 재계산
    for (let i = 0; i < routeList.value.length; i++) {
      routeList.value[i].order = i + 1
    }
    // 마커 아이콘과 클러스터를 갱신
    updateMarkers()
    emit('route-changed', routeList.value.slice())
    return
  }

  // 새 항목 추가
  const lat = toNumber(item.mapy)
  const lng = toNumber(item.mapx)
  const order = routeList.value.length + 1
  routeList.value.push({ contentid: id, title: item.title, lat, lng, order })
  // 마커 아이콘 갱신
  updateMarkers()
  emit('route-changed', routeList.value.slice())
}

function clearMarkers() {
  if (markersLayer && markersLayer.clearLayers) markersLayer.clearLayers()
  if (smallMarkersLayer && smallMarkersLayer.clearLayers) smallMarkersLayer.clearLayers()
  if (polylineLayer) {
    try { map?.removeLayer(polylineLayer) } catch (e) {}
    polylineLayer = null
  }
}

function updateMarkers() {
  if (!map || !markersLayer) return
  clearMarkers()
  const bounds = L.latLngBounds([])

  // If parent requested showing only a post's saved route, render only those markers
  if (showOnlyRoute.value) {
    if (!routeList.value.length) {
      // nothing to render; routeMessage will inform the user
      return
    }

    for (const r of routeList.value) {
      const lat = toNumber(r.lat)
      const lng = toNumber(r.lng)
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue

      const icon = buildMarkerIcon(r.order, true, true)
      const marker = L.marker([lat, lng], { icon, keyboard: true, title: r.title || '장소' })

      marker.bindTooltip(
        `<div class="localhub-tooltip-title">${escapeHtml(r.title || '장소')}</div>`,
        { direction: 'top', offset: [0, -9], opacity: 1 },
      )

      marker.on('click', () => {
        activeItem.value = null
        if (map) {
          try { beginProgrammaticMove(); map.setView([lat, lng], Math.max(map.getZoom(), 13), { animate: true }); map.once('moveend', () => persistMapView()); setTimeout(() => persistMapView(), 800) } catch (e) {}
        }
      })

      smallMarkersLayer.addLayer(marker)
      bounds.extend([lat, lng])
    }

      // draw polyline connecting route points (in order)
      try {
        const latlngs = routeList.value
          .map(r => [Number(r.lat), Number(r.lng)])
          .filter(([a, b]) => Number.isFinite(a) && Number.isFinite(b))
        if (latlngs.length > 1) {
          polylineLayer = L.polyline(latlngs, { color: '#6f49c8', weight: 4, opacity: 0.95, lineCap: 'round' })
          polylineLayer.addTo(map)
        }
      } catch (e) {}

    if (bounds.isValid()) {
        const now = Date.now()
        // avoid overriding recent user interactions and respect manual auto-fit toggle
        if (autoFitEnabled.value && now - lastUserInteraction.value > 500) {
            try {
            console.debug('MapView: updateMarkers route-only fitBounds', { autoFitEnabled: autoFitEnabled.value, lastUserInteraction: lastUserInteraction.value })
            beginProgrammaticMove()
            const padBounds = bounds.pad(0.08)
            const targetFrac = FIT_TARGET_FRAC
            // compute desired zoom from pixel sizes (more robust than zoomToFit inversion)
            const desiredZoom = computeDesiredZoomForTarget(padBounds, targetFrac)
            const center = padBounds.getCenter()
            if (desiredZoom == null) {
              // fallback: use zoomToFit adjusted by targetFrac (correct sign)
              const zoomToFit = (map as any).getBoundsZoom ? (map as any).getBoundsZoom(padBounds, false) : (map.getZoom() || 11)
              const maxZoomAllowed = typeof (map as any).getMaxZoom === 'function' ? (map as any).getMaxZoom() : 19
              const fallbackZoom = Math.min(zoomToFit + Math.log2(targetFrac), maxZoomAllowed)
              console.debug('MapView: route-only fallback fit', { zoomToFit, fallbackZoom, targetFrac, padBounds, mapSize: map.getSize(), center })
              map.setView(center, fallbackZoom, { animate: true })
            } else {
              console.debug('MapView: route-only fit', { desiredZoom, targetFrac, padBounds, mapSize: map.getSize(), center })
              map.setView(center, desiredZoom, { animate: true })
            }
            map.once('moveend', () => persistMapView())
            setTimeout(() => persistMapView(), 800)
          } catch (e) { console.debug('MapView: fitBounds failed', e) }
        } else {
          console.debug('MapView: skipping fitBounds (autoFitEnabled, lastUserInteraction)', { autoFitEnabled: autoFitEnabled.value, lastUserInteraction: lastUserInteraction.value })
        }
    }

    return
  }

  const entries: Array<{ item: TourItem; lat: number; lng: number; marker: L.Marker; point?: L.Point; isSelected?: boolean }> = []
  for (const item of visibleItems.value) {
    const lat = toNumber(item.mapy)
    const lng = toNumber(item.mapx)
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue

    const selectedIndex = routeList.value.findIndex(r => String(r.contentid) === String(item.contentid))
    const isSelected = selectedIndex >= 0
    const order = isSelected ? routeList.value[selectedIndex].order : undefined
    const icon = buildMarkerIcon(order, isSelected, !!props.routeMode || !!props.editingRoute)

    const marker = L.marker([lat, lng], { icon, keyboard: true, title: item.title || '관광지' })

    marker.bindTooltip(
      `<div class="localhub-tooltip-title">${escapeHtml(item.title || '관광지')}</div>`,
      { direction: 'top', offset: [0, -9], opacity: 1 },
    )

    marker.on('click', () => {
      if (props.routeMode || props.editingRoute) {
        // Toggle selection
        handleRouteMarkerClick(item)
        // Also open the same info panel as normal clicks
        activeItem.value = item
        if (map) {
          try { beginProgrammaticMove(); map.setView([lat, lng], Math.max(map.getZoom(), 13), { animate: true }); map.once('moveend', () => persistMapView()); setTimeout(() => persistMapView(), 800) } catch (e) { /* ignore */ }
        }
      } else {
        activeItem.value = item
        if (map) {
          try { beginProgrammaticMove(); map.setView([lat, lng], Math.max(map.getZoom(), 13), { animate: true }); map.once('moveend', () => persistMapView()) } catch (e) { /* ignore */ }
        }
      }
    })

    entries.push({ item, lat, lng, marker, isSelected })
    bounds.extend([lat, lng])
  }

  if (!bounds.isValid()) return

  for (const e of entries) {
    e.point = map.latLngToLayerPoint(L.latLng(e.lat, e.lng))
  }

  const threshold = CLUSTER_RADIUS_PX

  // Build clustering only for non-selected entries so selected markers are always shown
  const nonSelIndices = entries.map((_, i) => i).filter(i => !entries[i].isSelected)
  const m = nonSelIndices.length
  const adj: number[][] = Array.from({ length: m }, () => [])
  for (let a = 0; a < m; a++) {
    for (let b = a + 1; b < m; b++) {
      const i = nonSelIndices[a]
      const j = nonSelIndices[b]
      const dx = entries[i].point!.x - entries[j].point!.x
      const dy = entries[i].point!.y - entries[j].point!.y
      if (dx * dx + dy * dy <= threshold * threshold) {
        adj[a].push(b)
        adj[b].push(a)
      }
    }
  }

  const visited = new Array(m).fill(false)
  for (let a = 0; a < m; a++) {
    if (visited[a]) continue
    const stack = [a]
    visited[a] = true
    const compIdxs: number[] = []
    while (stack.length) {
      const cur = stack.pop()!
      compIdxs.push(nonSelIndices[cur])
      for (const nb of adj[cur]) {
        if (!visited[nb]) { visited[nb] = true; stack.push(nb) }
      }
    }

    if (compIdxs.length >= CLUSTER_MIN_SIZE) {
      for (const idx of compIdxs) markersLayer.addLayer(entries[idx].marker)
    } else {
      for (const idx of compIdxs) smallMarkersLayer.addLayer(entries[idx].marker)
    }
  }

  // Always add selected markers individually so they are never clustered
  for (let i = 0; i < entries.length; i++) {
    if (entries[i].isSelected) smallMarkersLayer.addLayer(entries[i].marker)
  }

    if (bounds.isValid()) {
      if (!initialFitDone) {
        const now = Date.now()
        if (autoFitEnabled.value && now - lastUserInteraction.value > 500) {
          try {
            console.debug('MapView: initial fitBounds', { autoFitEnabled: autoFitEnabled.value, lastUserInteraction: lastUserInteraction.value })
            beginProgrammaticMove()
            const padBounds = bounds.pad(0.08)
            const targetFrac = FIT_TARGET_FRAC
            const desiredZoom = computeDesiredZoomForTarget(padBounds, targetFrac)
            const center = padBounds.getCenter()
            if (desiredZoom == null) {
              const zoomToFit = (map as any).getBoundsZoom ? (map as any).getBoundsZoom(padBounds, false) : (map.getZoom() || 11)
              const maxZoomAllowed = typeof (map as any).getMaxZoom === 'function' ? (map as any).getMaxZoom() : 19
              const fallbackZoom = Math.min(zoomToFit + Math.log2(targetFrac), maxZoomAllowed)
              console.debug('MapView: initial fallback fit', { zoomToFit, fallbackZoom, targetFrac, padBounds, mapSize: map.getSize(), center })
              map.setView(center, fallbackZoom)
            } else {
              console.debug('MapView: initial fit', { desiredZoom, targetFrac, padBounds, mapSize: map.getSize(), center })
              map.setView(center, desiredZoom)
            }
            map.once('moveend', () => persistMapView())
            setTimeout(() => persistMapView(), 800)
          } catch (e) { console.debug('MapView: initial fitBounds failed', e) }
        } else {
          console.debug('MapView: skipping initial fitBounds', { autoFitEnabled: autoFitEnabled.value, lastUserInteraction: lastUserInteraction.value })
        }
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
    // entering route mode: try to restore previous selection from sessionStorage
    try {
      const raw = sessionStorage.getItem('localhub.routeSelection')
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed) && parsed.length) {
          routeList.value = parsed.map((r: any, i: number) => ({
            contentid: r.contentid, title: r.title, lat: r.lat, lng: r.lng, order: r.order ?? (i + 1)
          }))
        } else {
          routeList.value = []
        }
      } else {
        routeList.value = []
      }
    } catch (e) {
      routeList.value = []
    }
    emit('route-changed', routeList.value.slice())
  } else if (!val && oldVal) {
    // exiting route mode: preserve selections (PostForm may be open to edit)
    activeItem.value = null
    emit('route-changed', routeList.value.slice())
  }
  updateMarkers()
})

// MapView.vue: 부모가 선택/카메라 상태를 가져가거나 선택을 초기화, 카메라 리셋을 할 수 있도록 노출
defineExpose({
  exportSelection() {
    try { saveMapView() } catch (e) {}
    return {
      routeList: routeList.value.slice(),
      mapView: map ? { lat: map.getCenter().lat, lng: map.getCenter().lng, zoom: map.getZoom() } : null
    }
  },
  clearRoute() {
    routeList.value = []
    showOnlyRoute.value = false
    routeMessage.value = ''
    try { sessionStorage.removeItem('localhub.routeSelection') } catch (e) {}
    updateMarkers()
    emit('route-changed', routeList.value.slice())
  },
  showRouteFromPost(ids) {
    return showRouteFromPost(ids)
  },
  enableAutoFit() {
    try {
      autoFitEnabled.value = true
      lastUserInteraction.value = 0
      initialFitDone = false
      try { map?.invalidateSize() } catch (e) {}
      setTimeout(() => updateMarkers(), 80)
    } catch (e) {}
  },
  resetCamera() {
    if (!map) return
    try {
      beginProgrammaticMove()
      map.setView([37.5665, 126.978], 11, { animate: true })
      map.once('moveend', () => persistMapView())
    } catch (e) {}
    // remove stored camera so future mounts start from default
    try { sessionStorage.removeItem(STORAGE_KEY) } catch (e) {}
    initialFitDone = false
    updateMarkers()
  }
})

onMounted(async () => {
  if (!mapEl.value) return

  map = L.map(mapEl.value, {
    preferCanvas: true,
    zoomControl: false,
    attributionControl: true,
    // allow fractional (non-integer) zoom levels so computed desiredZoom can be fractional
    zoomSnap: 0,
    zoomDelta: 0.25,
  }).setView([37.5665, 126.978], 11)
  const saved = sessionStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const s = JSON.parse(saved)
      if (s && Number.isFinite(s.lat) && Number.isFinite(s.lng) && Number.isFinite(s.zoom)) {
        beginProgrammaticMove()
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
  // track user interactions to avoid programmatic fitBounds immediately after user moves
  map.on('movestart', () => { lastUserInteraction.value = Date.now(); autoFitEnabled.value = false })
  map.on('zoomstart', () => { lastUserInteraction.value = Date.now(); autoFitEnabled.value = false })
  map.on('dragstart', () => { lastUserInteraction.value = Date.now(); autoFitEnabled.value = false })
  map.on('touchstart', () => { lastUserInteraction.value = Date.now(); autoFitEnabled.value = false })

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
  lastUserInteraction.value = 0
})

function onMapMove() {
  if (!map) return
  // when showing a post's saved route, avoid fetching and re-fitting markers
  if (showOnlyRoute.value) return

  if (fetchTimer) clearTimeout(fetchTimer)
  fetchTimer = window.setTimeout(() => {
    if (!map) return
    void fetchPoisForBounds(map.getBounds())
  }, DEBOUNCE_MS)
}

function toggleAutoFit() {
  autoFitEnabled.value = !autoFitEnabled.value
  console.debug('MapView: toggleAutoFit ->', autoFitEnabled.value)
  if (autoFitEnabled.value) {
    // re-enable automatic fitting: reset interaction timer and trigger re-layout+fit
    lastUserInteraction.value = 0
    initialFitDone = false
    try { map?.invalidateSize() } catch (e) {}
    // small delay then update markers to cause fitBounds
    setTimeout(() => updateMarkers(), 80)
  }
}
</script>

<style scoped>
/* 기존 스타일 유지 */
.map-shell {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border-radius: 18px;
  background: #e9e6f0;
}

.map-canvas {
  width: 100%;
  height: 100%;
  min-height: 0;
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

.map-route-msg {
  position: absolute;
  z-index: 700;
  left: 50%;
  top: 18px;
  transform: translateX(-50%);
  max-width: min(640px, calc(100% - 56px));
  box-shadow: 0 12px 32px rgba(83, 29, 36, 0.06);
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

.map-route-summary {
  position: absolute;
  z-index: 860;
  right: 14px;
  bottom: 14px;
  width: 320px;
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