<template>
  <div>
    <div class="mb-2 flex justify-between items-center">
      <h3 class="text-sm font-medium text-gray-700">게시판</h3>
      <div class="text-xs text-gray-500">{{ visibleCount }} / {{ totalCount }}</div>
    </div>

    <div ref="scroller" class="h-[70vh] overflow-auto pr-2" @scroll="onScroll">
      <ul class="grid grid-cols-1 gap-2">
        <li v-for="post in visiblePosts" :key="post.id" class="border rounded overflow-hidden">
          <button
            @click="onToggle(post)"
            :aria-expanded="isExpanded(post.id)"
            class="w-full text-left p-3 flex justify-between items-start gap-2 hover:bg-gray-50 focus:outline-none"
          >
            <div>
              <div class="font-medium text-sm">{{ post.title }}</div>
              <div class="text-xs text-gray-400 mt-1">{{ formatDate(post.created_at) }}</div>
            </div>
            <div class="text-xs text-gray-600">{{ displayedCountFor(post) }} 조회</div>
          </button>

          <transition name="fade">
            <div v-if="isExpanded(post.id)" class="p-3 text-sm text-gray-700 border-t">
              {{ post.content }}
            </div>
          </transition>
        </li>
      </ul>

      <div v-if="loading" class="py-4 text-center text-sm text-gray-500">로딩 중...</div>
      <div v-else-if="!allLoaded" class="py-4 text-center text-sm text-gray-500">스크롤하여 더 불러오기...</div>
      <div v-else class="py-4 text-center text-sm text-gray-500">끝</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { incrementViewOptimistic, displayedViews, startBackgroundSync } from '../services/postService';

type Post = { id: string; title: string; content: string; created_at: string; views?: number };

const props = defineProps<{ filename?: string; pageSize?: number }>();
const filename = props.filename ?? 'mock_posts.json';
const pageSize = props.pageSize ?? 1;

const allPosts = ref<Post[]>([]);
const page = ref(1);
const loading = ref(false);
const scroller = ref<HTMLElement | null>(null);

const visiblePosts = computed(() => allPosts.value.slice(0, page.value * pageSize));
const visibleCount = computed(() => visiblePosts.value.length);
const totalCount = computed(() => allPosts.value.length);
const allLoaded = computed(() => visibleCount.value >= totalCount.value);

const expanded = ref(new Set<string>());

// displayedCounts: 로컬 낙관적 증가를 즉시 반영하기 위한 맵
const displayedCounts = ref<Record<string, number>>({});

function isExpanded(id: string) { return expanded.value.has(id); }

function displayedCountFor(post: Post) {
  return displayedCounts.value[post.id] ?? displayedViews(post.views ?? 0, post.id);
}

function onToggle(post: Post) {
  const s = new Set(expanded.value);
  const opening = !s.has(post.id);

  if (opening) {
    // 열 때만 조회수 낙관적 증가
    const newDisplayed = incrementViewOptimistic(post.id, post.views ?? 0);
    displayedCounts.value = { ...displayedCounts.value, [post.id]: newDisplayed };
  }

  if (s.has(post.id)) s.delete(post.id); else s.add(post.id);
  expanded.value = s;
}

async function loadAll() {
  loading.value = true;
  try {
    const res = await fetch(`/data/${filename}`);
    if (!res.ok) throw new Error('Failed to load posts');
    allPosts.value = await res.json();

    // 초기 표시값 세팅
    const initial: Record<string, number> = {};
    for (const p of allPosts.value) {
      initial[p.id] = displayedViews(p.views ?? 0, p.id);
    }
    displayedCounts.value = initial;
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function loadMore() { if (!allLoaded.value) page.value += 1; }
function onScroll() {
  if (!scroller.value || allLoaded.value) return;
  const el = scroller.value;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) loadMore();
}

function formatDate(s?: string) {
  if (!s) return '';
  const d = new Date(s);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

onMounted(async () => {
  // 시작: 데이터 로드 + 백그라운드 싱크 시작
  await loadAll();
  startBackgroundSync();
});
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>