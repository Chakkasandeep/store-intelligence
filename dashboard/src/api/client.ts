import { apiUrl, STORE_ID } from '../config';
import {
  normalizeAnomalies,
  normalizeFunnel,
  normalizeHeatmap,
  normalizeMetrics,
} from './normalize';
import type {
  HealthResponse,
  StoreAnomalies,
  StoreFunnel,
  StoreHeatmap,
  StoreMetrics,
} from '../types/api';

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(
      `API ${res.status} ${res.statusText}${body ? `: ${body.slice(0, 200)}` : ''}`,
    );
  }

  return res.json() as Promise<T>;
}

export async function getStoreMetrics(storeId = STORE_ID): Promise<StoreMetrics> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/stores/${encodeURIComponent(storeId)}/metrics`,
  );
  return normalizeMetrics(raw);
}

export async function getStoreFunnel(storeId = STORE_ID): Promise<StoreFunnel> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/stores/${encodeURIComponent(storeId)}/funnel`,
  );
  return normalizeFunnel(raw);
}

export async function getStoreHeatmap(storeId = STORE_ID): Promise<StoreHeatmap> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/stores/${encodeURIComponent(storeId)}/heatmap`,
  );
  return normalizeHeatmap(raw);
}

export async function getStoreAnomalies(storeId = STORE_ID): Promise<StoreAnomalies> {
  const raw = await fetchJson<Record<string, unknown>>(
    `/stores/${encodeURIComponent(storeId)}/anomalies`,
  );
  return normalizeAnomalies(raw);
}

export function getHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>('/health');
}
