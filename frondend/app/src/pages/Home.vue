<template>
  <div class="home-page">
    <section class="home-intro" aria-labelledby="home-title">
      <div>
        <div class="eyebrow">
          <span class="eyebrow-dot"></span>
          Seoul local discovery
        </div>

        <h1 id="home-title" class="page-title">
          서울을 발견하고,<br />
          <span>나만의 코스로 연결하세요.</span>
        </h1>

        <p class="page-description home-copy">
          지도에서 새로운 장소를 찾고, 다른 여행자의 생생한 이야기를
          참고해보세요.
        </p>
      </div>

      <div class="intro-guide" aria-label="서비스 이용 안내">
        <div class="guide-icon">
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M9 18 3.8 20.6A.55.55 0 0 1 3 20.1V6.8a1 1 0 0 1 .55-.9L9 3.2m0 14.8 6 3m-6-3V3.2m6 17.8 5.45-2.7a1 1 0 0 0 .55-.9V4.1a.55.55 0 0 0-.8-.5L15 6.2m0 14.8V6.2M9 3.2l6 3"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>

        <div>
          <strong>지도 핀을 눌러보세요</strong>
          <span>관광지 상세 정보로 바로 이동할 수 있어요.</span>
        </div>
      </div>
    </section>

    <section class="workspace" aria-label="서울 관광 지도와 커뮤니티">
      <aside class="feed-panel surface-card">
        <div class="panel-header">
          <div v-if="!composing">
            <div class="eyebrow">Community</div>
            <h2 class="panel-title">지금 서울 이야기</h2>
            <p class="panel-description">
              여행자들이 방금 공유한 장소와 팁
            </p>
          </div>

          <div class="panel-actions" style="display:inline-flex;gap:8px;align-items:center">
            <button
              v-if="!composing"
              type="button"
              class="icon-button"
              aria-label="새 글 쓰기"
              title="새 글 쓰기"
              @click="openComposer"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
                <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>

            <button
              v-if="!composing"
              type="button"
              class="icon-button"
              title="경로로 글쓰기"
              @click="startComposerFromRoute"
            >
              <svg viewBox="0 0 24 24" width="15" height="15" fill="none" aria-hidden="true">
                <path d="M3 21v-3l11-11 3 3L9 21H3z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <button
              v-else
              type="button"
              class="icon-button"
              title="작성 취소"
              @click="onComposerCancel"
            >
              ×
            </button>
          </div>
        </div>

        <div class="soft-divider"></div>

        <div v-if="composing" style="padding:12px;">
          <PostForm :key="editingPostId ?? 'compose'" :embedded="true" :id="editingPostId" :routeSelection="currentRoute" @cancel="onComposerCancel" @submitted="onComposerSubmitted" />
        </div>

        <div v-else-if="viewingPostId" style="padding:12px;">
          <PostDetail :embedded="true" :id="viewingPostId" @close="onClosePost" @edit-post="onEditFromDetail" @show-route="onShowRoute" />
        </div>

        <div v-else>
          <BoardList :key="boardKey" :filename="boardFilename" :page-size="3" @open-post="onOpenPost" />
        </div>
      </aside>

      <section class="map-panel surface-card">
        <div class="map-panel-header">
          <div>
            <div class="eyebrow">Explore map</div>
            <h2 class="panel-title">서울 관광 지도</h2>
          </div>

          <div class="map-panel-actions">
            <button
              type="button"
              :class="['btn', routeMode ? 'btn-inverted' : 'btn-primary']"
              @click="onCreateRoute"
            >
              {{ routeMode ? '코스 선택 완료' : composing ? '코스 수정' : '여행 경로 만들기' }}
            </button>
          </div>

          <div class="status-chip">
            <span class="status-dot"></span>
            관광지 데이터 연결됨
          </div>
        </div>

        <MapView ref="mapViewRef" filename="서울_여행코스.json" :routeMode="routeMode" :editingRoute="composing" @route-changed="onRouteChanged" />
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BoardList from '../components/BoardList.vue'
import MapView from '../components/MapView.vue'
import PostForm from './PostForm.vue'
import PostDetail from './PostDetail.vue'

// route selection mode (지도에서 장소를 선택하는 모드)
const routeMode = ref(false)
// 내부적으로 MapView에서 emit 되는 현재 routeList (선택 중간 상태)
const currentRoute = ref<any[]>([])

// feed-panel 쪽 composer 표시 상태 (true이면 PostForm을 feed-panel에 렌더)
const composing = ref(false)

// 왼쪽 패널에서 보고 있는 게시글 ID (embedded detail)
const viewingPostId = ref<string | null>(null)

// 편집 중인 게시글 ID (embedded PostForm 편집 모드)
const editingPostId = ref<string | undefined>(undefined)

// BoardList를 강제 리로드할 때 변경하는 키
const boardKey = ref<number>(0)
const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'
const boardFilename = `${API_BASE}/posts?limit=20`

// ref to MapView component to call exportSelection()
const mapViewRef = ref<any>(null)

const route = useRoute()
const router = useRouter()

function openComposer() {
  editingPostId.value = undefined
  composing.value = true
}

// route query로도 composer를 열 수 있게 (헤더에서 홈으로 이동할 때 사용)
watch(() => route.query.compose, (val) => {
  if (val === '1' || val === 'true') {
    composing.value = true
    // 쿼리 제거해서 URL 깨끗하게 유지
    router.replace({ name: 'Home', query: {} }).catch(() => {})
  }
})

function startComposerFromRoute() {
  // shortcut: 바로 글쓰기(선택한 게 있으면 composer 열기), 또는 토글 없이 사용 가능
  routeMode.value = true
  composing.value = false
}

// 버튼: 경로 모드 토글 / 완료 처리
function onCreateRoute() {
  if (!routeMode.value) {
    routeMode.value = true
    composing.value = false
    return
  }

  // routeMode 가 켜진 상태에서 버튼을 다시 누르면 '완료' 동작
  const exportData = mapViewRef.value?.exportSelection?.()
  const selected = exportData?.routeList ?? currentRoute.value ?? []
  const mapView = exportData?.mapView ?? null

  if (!selected || selected.length === 0) {
    routeMode.value = false
    alert('선택한 장소가 없습니다.')
    return
  }

  try {
    sessionStorage.setItem('localhub.routeSelection', JSON.stringify(selected))
    if (mapView) sessionStorage.setItem('localhub.mapview', JSON.stringify({ ...mapView, ts: Date.now() }))
  } catch (e) {}

  // 닫고 feed-panel에 composer 표시
  routeMode.value = false
  composing.value = true
}

// MapView로부터 route 변경 수신
function onRouteChanged(list: any[]) {
  currentRoute.value = list
  // composer가 열려있으면 선택 목록을 sessionStorage에 즉시 반영해서 PostForm와 동기화
  if (composing.value) {
    try { sessionStorage.setItem('localhub.routeSelection', JSON.stringify(list)) } catch (e) {}
  }
}

// composer 이벤트 핸들러
function onComposerCancel() {
  composing.value = false
  // 보드 새로고침 트리거 (key 변경)
  boardKey.value = Date.now()
  if (editingPostId.value) {
    // return to the post detail we were editing
    viewingPostId.value = editingPostId.value
    editingPostId.value = undefined
  } else {
    viewingPostId.value = null
  }
}

function onEditFromDetail(id: string) {
  editingPostId.value = id
  composing.value = true
  viewingPostId.value = null
}

function onShowRoute(route: any[]) {
  try {
    // give MapView the array of contentids (may be empty)
    mapViewRef.value?.showRouteFromPost?.(route ?? [])
  } catch (e) {}
}

function onOpenPost(id: string) {
  viewingPostId.value = id
  composing.value = false
  try { mapViewRef.value?.enableAutoFit?.() } catch (e) {}
}

function onClosePost() {
  viewingPostId.value = null
  try { mapViewRef.value?.clearRoute?.() } catch (e) {}
}

function onComposerSubmitted() {
  composing.value = false
  // BoardList를 새로고침
  boardKey.value = Date.now()
  // 선택 데이터는 제거
  try { sessionStorage.removeItem('localhub.routeSelection') } catch(e) {}
  // 지도 선택도 초기화
  try { mapViewRef.value?.clearRoute?.() } catch (e) {}
  // 카메라를 초기 상태로 되돌림
  try { mapViewRef.value?.resetCamera?.() } catch (e) {}
  editingPostId.value = undefined
}
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 26px;
  height: 100%;
  min-height: 0;
}

.home-intro {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 36px;
  padding: 16px 6px 6px;
}

.eyebrow-dot {
  width: 8px;
  height: 8px;

  border-radius: 999px;

  background: linear-gradient(135deg, #9b6ee5, #6032ad);
  box-shadow: 0 0 0 5px rgba(139, 91, 221, 0.1);
}

.page-title {
  margin-top: 11px;
}

.page-title span {
  color: transparent;

  background: linear-gradient(
    100deg,
    #4b278f 0%,
    #8050cf 58%,
    #4b65bf 100%
  );

  background-clip: text;
  -webkit-background-clip: text;
}

.home-copy {
  max-width: 620px;
  margin-top: 16px;
}

.intro-guide {
  width: min(360px, 100%);
  padding: 14px 16px;
  flex: 0 0 auto;

  display: flex;
  align-items: center;
  gap: 13px;

  border: 1px solid rgba(226, 229, 238, 0.95);
  border-radius: 17px;

  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 8px 26px rgba(39, 28, 70, 0.05);

  backdrop-filter: blur(12px);
}

.guide-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;

  display: grid;
  place-items: center;

  border-radius: 13px;

  color: #6b3bb4;
  background: #f1ecfa;
}

.intro-guide strong,
.intro-guide span {
  display: block;
}

.intro-guide strong {
  color: #2a3040;
  font-size: 13px;
  font-weight: 800;
}

.intro-guide span {
  margin-top: 3px;

  color: #8a92a3;
  font-size: 11px;
  line-height: 1.5;
}

.workspace {
  /* let workspace fill remaining vertical space */
  flex: 1 1 auto;
  min-height: 0;

  display: grid;
  grid-template-columns: minmax(300px, 355px) minmax(0, 1fr);
  gap: 18px;
  overflow: hidden;
}

.feed-panel,
.map-panel {
  min-width: 0;
}

.feed-panel {
  display: flex;
  flex-direction: column;
  overflow: auto;
  min-height: 0;
}

.map-panel {
  padding: 8px;

  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
}

.map-panel-header {
  padding: 12px 12px 16px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.map-panel-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.map-panel-header .panel-title {
  margin-top: 3px;
}

.btn-inverted {
  background-color: #ffffff;
  color: transparent;
  background-image: linear-gradient(135deg, var(--brand-600), var(--brand-800));
  -webkit-background-clip: text;
  background-clip: text;
  border: 1px solid rgba(75, 39, 143, 0.08);
  box-shadow: none;
}

.btn-inverted:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(96, 50, 173, 0.12);
}

@media (max-width: 960px) {
  .home-intro {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }

  .intro-guide {
    width: 100%;
  }

  .workspace {
    grid-template-columns: 1fr;
  }

  .feed-panel {
    max-height: none;
  }
}

@media (max-width: 640px) {
  .home-page {
    gap: 20px;
  }

  .home-intro {
    padding-inline: 2px;
  }

  .workspace {
    gap: 14px;
  }

  .status-chip {
    display: none;
  }

  .map-panel-header {
    padding: 10px 10px 14px;
  }
}
</style>