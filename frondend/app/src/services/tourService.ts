import type { TourApiResponse, TourItem } from '../types/tour';

const cache = new Map<string, TourApiResponse>();

// 간단한 서울 bbox (필요시 조정)
const BOUNDS = {
  latMin: 37.428,
  latMax: 37.701,
  lngMin: 126.764,
  lngMax: 127.183,
};

function parseNum(v?: unknown): number | null {
  if (v === undefined || v === null) return null;
  const s = String(v).trim();
  if (s === '') return null;
  const n = Number(s.replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export async function fetchTourData(filename: string): Promise<TourApiResponse> {
  const key = filename;
  if (cache.has(key)) return cache.get(key)!;

  let json: TourApiResponse;

  // 1) 먼저 API 시도 (백엔드가 제공하면 여기로)
  try {
    const apiRes = await fetch(`${API_BASE}/tours?filename=${encodeURIComponent(filename)}`);
    if (!apiRes.ok) throw new Error(`API error ${apiRes.status}`);
    json = (await apiRes.json()) as TourApiResponse;
  } catch {
    // 2) API 실패하면 정적 파일로 폴백
    const res = await fetch(`/data/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error(`Failed to load ${filename} (${res.status})`);
    json = (await res.json()) as TourApiResponse;
  }

  // 기존 정제 로직 재사용
  if (Array.isArray(json.items)) {
    const sanitized: TourItem[] = [];

    for (const it of json.items) {
      if (!it || !it.contentid || !it.title) continue;

      const lat = parseNum(it.mapy);
      const lng = parseNum(it.mapx);
      const coordValid = lat !== null && lng !== null;
      const inBounds =
        coordValid &&
        lat >= BOUNDS.latMin && lat <= BOUNDS.latMax &&
        lng >= BOUNDS.lngMin && lng <= BOUNDS.lngMax;

      const copy: TourItem = { ...it, disabled: !inBounds };
      sanitized.push(copy);
    }

    json.items = sanitized;
  }

  cache.set(key, json);
  return json;
}

export async function getAllItems(
  filename = '서울_관광지.json',
  options?: { includeDisabled?: boolean }
): Promise<TourItem[]> {
  const data = await fetchTourData(filename);
  const includeDisabled = options?.includeDisabled ?? false;
  const items = data.items ?? [];
  return includeDisabled ? items : items.filter((it) => !it.disabled);
}

export async function getItemById(
  filename: string,
  id: string,
  options?: { includeDisabled?: boolean }
): Promise<TourItem | undefined> {
  const includeDisabled = options?.includeDisabled ?? false;
  if (includeDisabled) {
    const data = await fetchTourData(filename);
    return (data.items ?? []).find((it) => it.contentid === id);
  }
  const items = await getAllItems(filename, { includeDisabled: false });
  return items.find((it) => it.contentid === id);
}