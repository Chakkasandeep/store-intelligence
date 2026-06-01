const rawApi = import.meta.env.VITE_API_URL?.trim();
const rawStore = import.meta.env.VITE_STORE_ID?.trim();

/** Empty in production build = same origin (HF Space / single-container Docker). */
export const API_BASE_URL =
  rawApi && rawApi.length > 0
    ? rawApi
    : import.meta.env.PROD
      ? ''
      : 'http://localhost:8000';
export const STORE_ID = rawStore && rawStore.length > 0 ? rawStore : 'ST1008';

export function apiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (import.meta.env.DEV) {
    return `/api${normalized}`;
  }
  const base = API_BASE_URL.replace(/\/$/, '');
  return base ? `${base}${normalized}` : normalized;
}

export function wsMetricsUrl(): string {
  if (!API_BASE_URL && import.meta.env.PROD && typeof window !== 'undefined') {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/ws/metrics`;
  }
  const base = (API_BASE_URL || 'http://localhost:8000').replace(/^http/, 'ws').replace(/\/$/, '');
  return `${base}/ws/metrics`;
}
