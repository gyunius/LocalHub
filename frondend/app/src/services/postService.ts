type QueueItem = { id: string; delta: number; ts: number };

const LS_VIEWS_KEY = 'lh:post_views';
const LS_QUEUE_KEY = 'lh:post_views_queue';

let syncRunning = false;
let syncStarted = false;
let onlineListener: (() => void) | null = null;
let intervalId: number | null = null;

function loadViewsMap(): Record<string, number> {
  try { return JSON.parse(localStorage.getItem(LS_VIEWS_KEY) ?? '{}'); } catch { return {}; }
}
function saveViewsMap(m: Record<string, number>) { localStorage.setItem(LS_VIEWS_KEY, JSON.stringify(m)); }

function loadQueue(): QueueItem[] {
  try { return JSON.parse(localStorage.getItem(LS_QUEUE_KEY) ?? '[]'); } catch { return []; }
}
function saveQueue(q: QueueItem[]) { localStorage.setItem(LS_QUEUE_KEY, JSON.stringify(q)); }

export function getLocalIncrement(id: string): number {
  const m = loadViewsMap();
  return m[id] ?? 0;
}

export function displayedViews(base = 0, id?: string): number {
  return base + (id ? getLocalIncrement(id) : 0);
}

/**
 * 낙관적 증가: 로컬 카운트 증가 + 큐에 추가(백엔드에 전송 시도)
 * 반환: 즉시 반영할 총 표시값 (base + 로컬증가)
 */
export function incrementViewOptimistic(id: string, base = 0): number {
  const m = loadViewsMap();
  m[id] = (m[id] ?? 0) + 1;
  saveViewsMap(m);

  const q = loadQueue();
  q.push({ id, delta: 1, ts: Date.now() });
  saveQueue(q);

  // 즉시 한 번 동기 시도(비동기)
  void flushQueueOnce();

  return base + m[id];
}

/**
 * 큐를 백엔드로 전송 (한 번만 실행)
 * - 서버 엔드포인트 가정: POST /api/posts/:id/views  body: { delta: number }
 * - 실패 시 큐에 남겨두고 나중에 재시도
 */
export async function flushQueueOnce(): Promise<void> {
  if (syncRunning) return;
  const q = loadQueue();
  if (q.length === 0) return;
  if (!navigator.onLine) return;

  syncRunning = true;
  try {
    // 합쳐서 id별 delta 계산
    const byId = q.reduce<Record<string, number>>((acc, it) => {
      acc[it.id] = (acc[it.id] ?? 0) + it.delta;
      return acc;
    }, {});

    // 순차 전송 (간단하고 안전)
    for (const id of Object.keys(byId)) {
      const delta = byId[id];
      try {
        const res = await fetch(`/api/posts/${encodeURIComponent(id)}/views`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ delta })
        });
        if (res.ok) {
          // 성공하면 해당 id 항목들을 큐에서 제거
          const remaining = loadQueue().filter((it) => it.id !== id);
          saveQueue(remaining);
        } else {
          // 서버 에러면 보류 (다음 시도 때 다시 시도)
          console.warn('View sync failed for', id, res.status);
        }
      } catch (e) {
        console.warn('Network error while syncing views for', id, e);
        // 네트워크 문제면 보류
      }
    }
  } finally {
    syncRunning = false;
  }
}

/**
 * 백그라운드 반복/온라인 이벤트로 큐 플러시를 시도합니다.
 * 여러번 호출되어도 내부에서 한 번만 시작합니다.
 */
export function startBackgroundSync(pollIntervalMs = 30_000) {
  if (syncStarted) return;
  syncStarted = true;

  onlineListener = () => void flushQueueOnce();
  window.addEventListener('online', onlineListener);

  intervalId = window.setInterval(() => {
    if (navigator.onLine) void flushQueueOnce();
  }, pollIntervalMs);

  // 시작시 즉시 시도
  if (navigator.onLine) void flushQueueOnce();
}

export function stopBackgroundSync() {
  if (onlineListener) window.removeEventListener('online', onlineListener);
  if (intervalId) clearInterval(intervalId);
  syncStarted = false;
  onlineListener = null;
  intervalId = null;
}

// API helper (추가)
const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export type PostItem = { id: string; title: string; content: string; created_at: string; views?: number; };

export async function fetchPosts(page = 1, limit = 20): Promise<PostItem[]> {
  try {
    const res = await fetch(`${API_BASE}/posts?page=${page}&limit=${limit}`);
    if (!res.ok) throw new Error(await res.text());
    const json = await res.json();
    return Array.isArray(json) ? json : (json.items ?? []);
  } catch (apiErr) {
    // 폴백: 로컬 mock 파일
    try {
      const fileRes = await fetch(`/data/mock_posts.json`);
      if (!fileRes.ok) throw apiErr;
      const mock = await fileRes.json();
      return Array.isArray(mock) ? mock : (mock.items ?? []);
    } catch {
      throw apiErr;
    }
  }
}

export async function fetchPost(id: string): Promise<PostItem> {
  try {
    const res = await fetch(`${API_BASE}/posts/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  } catch (apiErr) {
    // 폴백: 로컬 mock 파일에서 id로 검색
    try {
      const fileRes = await fetch(`/data/mock_posts.json`);
      if (!fileRes.ok) throw apiErr;
      const data = await fileRes.json() as PostItem[] | { items?: PostItem[] };
      const list = Array.isArray(data) ? data : (data.items ?? []);
      const found = list.find(p => p.id === id);
      if (!found) throw new Error('Post not found in mock data');
      return found;
    } catch {
      throw apiErr;
    }
  }
}

export async function createPost(payload: { title: string; content: string; password: string; }): Promise<PostItem> {
  const res = await fetch(`${API_BASE}/posts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updatePost(id: string, payload: { title?: string; content?: string; password: string; }): Promise<PostItem> {
  const res = await fetch(`${API_BASE}/posts/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (res.status === 403) throw new Error('비밀번호가 틀렸습니다');
  if (!res.ok) throw new Error(await res.text());
  if (res.status === 204) return fetchPost(id);
  return res.json();
}

export async function deletePost(id: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/posts/${encodeURIComponent(id)}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  if (res.status === 403) throw new Error('비밀번호가 틀렸습니다');
  if (!res.ok) throw new Error(await res.text());
}

export async function verifyPostPassword(id: string, password: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/posts/${encodeURIComponent(id)}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  if (res.ok) return true;
  if (res.status === 403) return false;
  throw new Error(await res.text());
}