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

export async function fetchTourData(filename: string): Promise<TourApiResponse> {
  const key = filename;
  if (cache.has(key)) return cache.get(key)!;
  // Try backend API first (proxied to backend by Vite dev server), fallback to static public data
  let json: any = null;
  try {
    const apiRes = await fetch(`/api/pois?limit=10000`);
    if (apiRes.ok) {
      const apiJson = await apiRes.json();
      // apiJson.items is list of POI objects -- convert to TourApiResponse shape
      const items = (apiJson.items || []).map((it: any) => ({
        ...it,
        contentid: it.contentid,
        title: it.title,
        mapx: it.mapx,
        mapy: it.mapy,
        addr1: it.addr1,
      }));
      json = { items };
    }
  } catch (e) {
    // ignore and fallback
  }

  if (!json) {
    const res = await fetch(`/data/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error(`Failed to load ${filename} (${res.status})`);
    json = await res.json();
  }

  if (Array.isArray(json.items)) {
    const sanitized: TourItem[] = [];

    for (const it of json.items) {
      // 핵심 필드 없으면 제거
      if (!it || !it.contentid || !it.title) continue;

      const lat = parseNum(it.mapy);
      const lng = parseNum(it.mapx);
      const coordValid = lat !== null && lng !== null;
      const inBounds =
        coordValid &&
        lat >= BOUNDS.latMin && lat <= BOUNDS.latMax &&
        lng >= BOUNDS.lngMin && lng <= BOUNDS.lngMax;

      // 원본 손상 방지용 얕은 복사 + disabled 플래그
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