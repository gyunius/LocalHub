<template>
  <div class="board-list">
    <div class="board-meta">
      <span>전체 이야기</span>
      <span class="count-badge">{{ visibleCount }} / {{ totalCount }}</span>
    </div>

    <div
      ref="scroller"
      class="post-scroller pretty-scrollbar"
      @scroll="onScroll"
    >
      <div v-if="loading" class="empty-state">
        <div>
          <div class="loading-ring mx-auto"></div>
          <p class="mt-3">이야기를 불러오는 중이에요.</p>
        </div>
      </div>

      <ul v-else-if="visiblePosts.length" class="post-list">
        <li
          v-for="post in visiblePosts"
          :key="post.id"
          class="post-card"
        >
          <div class="post-card-top">
            <span class="post-category">여행 이야기</span>

            <span class="post-date">
              <svg
                viewBox="0 0 24 24"
                width="13"
                height="13"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M7 3v3m10-3v3M4.5 9h15M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Z"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>

              {{ formatDate(post.created_at) }}
            </span>
          </div>

          <router-link
            :to="{ name: 'PostDetail', params: { id: post.id } }"
            class="post-title"
          >
            {{ post.title }}
          </router-link>

          <p v-if="!isExpanded(post.id)" class="post-preview">
            {{ post.content }}
          </p>

          <transition name="reveal">
            <p v-if="isExpanded(post.id)" class="post-content">
              {{ post.content }}
            </p>
          </transition>

          <div class="post-footer">
            <span class="view-count">
              <svg
                viewBox="0 0 24 24"
                width="15"
                height="15"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M2.8 12s3.3-5.5 9.2-5.5 9.2 5.5 9.2 5.5-3.3 5.5-9.2 5.5S2.8 12 2.8 12Z"
                  stroke="currentColor"
                  stroke-width="1.7"
                  stroke-linejoin="round"
                />

                <circle
                  cx="12"
                  cy="12"
                  r="2.4"
                  stroke="currentColor"
                  stroke-width="1.7"
                />
              </svg>

              {{ displayedCountFor(post) }}
            </span>

            <button
              type="button"
              class="expand-button"
              @click="onToggle(post)"
            >
              {{ isExpanded(post.id) ? '접기' : '미리보기' }}

              <svg
                viewBox="0 0 24 24"
                width="14"
                height="14"
                fill="none"
                :class="{ rotated: isExpanded(post.id) }"
                aria-hidden="true"
              >
                <path
                  d="m7 10 5 5 5-5"
                  stroke="currentColor"
                  stroke-width="1.9"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>
          </div>
        </li>
      </ul>

      <div v-else class="empty-state">
        <div>
          <div class="empty-icon">
            <svg
              viewBox="0 0 24 24"
              width="22"
              height="22"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M6 4h12a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-7l-4.5 3v-3H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linejoin="round"
              />
            </svg>
          </div>

          <p>아직 등록된 이야기가 없습니다.</p>
        </div>
      </div>

      <div
        v-if="!loading && visiblePosts.length"
        class="list-status"
      >
        <span v-if="!allLoaded">
          스크롤하면 더 많은 이야기를 볼 수 있어요.
        </span>

        <span v-else>
          모든 이야기를 확인했어요.
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  displayedViews,
  incrementViewOptimistic,
  startBackgroundSync,
} from '../services/postService'

type Post = {
  id: string
  title: string
  content: string
  created_at: string
  views?: number
}

const props = defineProps<{
  filename?: string
  pageSize?: number
}>()

const filename = props.filename ?? 'mock_posts.json'
const pageSize = props.pageSize ?? 3

const allPosts = ref<Post[]>([])
const page = ref(1)
const loading = ref(false)
const scroller = ref<HTMLElement | null>(null)

const visiblePosts = computed(() =>
  allPosts.value.slice(0, page.value * pageSize),
)

const visibleCount = computed(() => visiblePosts.value.length)
const totalCount = computed(() => allPosts.value.length)

const allLoaded = computed(
  () => visibleCount.value >= totalCount.value,
)

const expanded = ref(new Set<string>())

const displayedCounts = ref<Record<string, number>>({})

function isExpanded(id: string) {
  return expanded.value.has(id)
}

function displayedCountFor(post: Post) {
  return (
    displayedCounts.value[post.id] ??
    displayedViews(post.views ?? 0, post.id)
  )
}

function onToggle(post: Post) {
  const next = new Set(expanded.value)
  const opening = !next.has(post.id)

  if (opening) {
    const newDisplayed = incrementViewOptimistic(
      post.id,
      post.views ?? 0,
    )

    displayedCounts.value = {
      ...displayedCounts.value,
      [post.id]: newDisplayed,
    }

    next.add(post.id)
  } else {
    next.delete(post.id)
  }

  expanded.value = next
}

async function loadAll() {
  loading.value = true

  try {
    const response = await fetch(`/data/${filename}`)

    if (!response.ok) {
      throw new Error('Failed to load posts')
    }

    allPosts.value = await response.json()

    const initial: Record<string, number> = {}

    for (const post of allPosts.value) {
      initial[post.id] = displayedViews(
        post.views ?? 0,
        post.id,
      )
    }

    displayedCounts.value = initial
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!allLoaded.value) {
    page.value += 1
  }
}

function onScroll() {
  if (!scroller.value || allLoaded.value) {
    return
  }

  const element = scroller.value

  const reachedBottom =
    element.scrollTop + element.clientHeight >=
    element.scrollHeight - 80

  if (reachedBottom) {
    loadMore()
  }
}

function formatDate(value?: string) {
  if (!value) {
    return ''
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}.${month}.${day}`
}

onMounted(async () => {
  await loadAll()
  startBackgroundSync()
})
</script>

<style scoped>
.board-list {
  min-height: 0;

  display: flex;
  flex: 1;
  flex-direction: column;
}

.board-meta {
  padding: 14px 20px 10px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  color: #8a92a3;
  font-size: 11px;
  font-weight: 700;
}

.post-scroller {
  min-height: 0;
  max-height: 568px;
  padding: 4px 12px 12px;

  overflow-y: auto;
}

.post-list {
  margin: 0;
  padding: 0;

  display: grid;
  gap: 10px;

  list-style: none;
}

.post-card {
  padding: 16px;

  border: 1px solid #e8eaf0;
  border-radius: 17px;

  background: #ffffff;

  transition:
    transform 160ms ease,
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.post-card:hover {
  transform: translateY(-2px);

  border-color: #ddd4ef;

  box-shadow: 0 10px 26px rgba(46, 31, 76, 0.08);
}

.post-card-top,
.post-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.post-category {
  color: #7444bd;
  font-size: 10px;
  font-weight: 850;
  letter-spacing: 0.04em;
}

.post-date,
.view-count {
  display: inline-flex;
  align-items: center;
  gap: 5px;

  color: #98a2b3;
  font-size: 10px;
  font-weight: 650;
}

.post-title {
  margin-top: 10px;

  display: block;

  color: #252b3b;
  font-size: 14px;
  font-weight: 820;
  letter-spacing: -0.025em;
  line-height: 1.45;

  transition: color 150ms ease;
}

.post-title:hover {
  color: #6032ad;
}

.post-preview,
.post-content {
  margin: 8px 0 0;

  color: #7a8292;
  font-size: 12px;
  line-height: 1.65;
}

.post-preview {
  display: -webkit-box;
  overflow: hidden;

  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.post-content {
  padding: 11px 12px;

  border-radius: 11px;

  color: #5f6879;
  background: #f8f8fb;
}

.post-footer {
  margin-top: 13px;
  padding-top: 12px;

  border-top: 1px solid #f0f1f5;
}

.expand-button {
  padding: 4px 0 4px 8px;

  display: inline-flex;
  align-items: center;
  gap: 3px;

  border: 0;

  color: #7d5ab2;
  background: transparent;

  cursor: pointer;

  font-size: 10px;
  font-weight: 800;
}

.expand-button svg {
  transition: transform 160ms ease;
}

.expand-button svg.rotated {
  transform: rotate(180deg);
}

.list-status {
  padding: 18px 8px 9px;

  color: #a0a6b2;
  text-align: center;
  font-size: 10px;
  font-weight: 650;
}

.empty-icon {
  width: 46px;
  height: 46px;
  margin: 0 auto 10px;

  display: grid;
  place-items: center;

  border-radius: 15px;

  color: #8962c3;
  background: #f1ecfa;
}

.reveal-enter-active,
.reveal-leave-active {
  transition:
    opacity 160ms ease,
    transform 160ms ease;
}

.reveal-enter-from,
.reveal-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

@media (max-width: 960px) {
  .post-scroller {
    max-height: 430px;
  }
}
</style>