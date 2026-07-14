import type { TourApiResponse, TourItem } from '../types/tour';

const cache = new Map<string, TourApiResponse>();

export async function fetchTourData(filename: string): Promise<TourApiResponse> {
  const key = filename;
  if (cache.has(key)) return cache.get(key)!;
  const res = await fetch(`/data/${encodeURIComponent(filename)}`);
  if (!res.ok) throw new Error(`Failed to load ${filename} (${res.status})`);
  const json = (await res.json()) as TourApiResponse;
  cache.set(key, json);
  return json;
}

export async function getAllItems(filename = '서울_관광지.json'): Promise<TourItem[]> {
  const data = await fetchTourData(filename);
  return data.items ?? [];
}

export async function getItemById(filename: string, id: string): Promise<TourItem | undefined> {
  const items = await getAllItems(filename);
  return items.find((it) => it.contentid === id);
}