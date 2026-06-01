import { useCallback, useEffect, useRef, useState } from 'react';
import { getStoreMetrics } from '../api/client';
import { parseMetricsPayload } from '../api/normalize';
import { STORE_ID, wsMetricsUrl } from '../config';
import type { StoreMetrics } from '../types/api';

const POLL_INTERVAL_MS = 10_000;
const WS_RECONNECT_MS = 3_000;

export type ConnectionMode = 'websocket' | 'polling' | 'connecting' | 'offline';

export interface LiveMetricsState {
  metrics: StoreMetrics | null;
  mode: ConnectionMode;
  error: string | null;
  lastUpdated: Date | null;
}

function parseWsMessage(raw: string): StoreMetrics | null {
  return parseMetricsPayload(raw);
}

export function useLiveMetrics(storeId = STORE_ID): LiveMetricsState {
  const [metrics, setMetrics] = useState<StoreMetrics | null>(null);
  const [mode, setMode] = useState<ConnectionMode>('connecting');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsActiveRef = useRef(false);

  const applyMetrics = useCallback((data: StoreMetrics) => {
    setMetrics(data);
    setLastUpdated(new Date());
    setError(null);
  }, []);

  const poll = useCallback(async () => {
    try {
      const data = await getStoreMetrics(storeId);
      applyMetrics(data);
      if (!wsActiveRef.current) {
        setMode('polling');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load metrics';
      setError(message);
      if (!wsActiveRef.current) {
        setMode('offline');
      }
    }
  }, [applyMetrics, storeId]);

  useEffect(() => {
    let cancelled = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const startPolling = () => {
      if (pollRef.current) return;
      void poll();
      pollRef.current = setInterval(() => {
        void poll();
      }, POLL_INTERVAL_MS);
    };

    const stopPolling = () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };

    const connectWs = () => {
      if (cancelled) return;

      const url = `${wsMetricsUrl()}?store_id=${encodeURIComponent(storeId)}`;
      setMode('connecting');

      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          if (cancelled) return;
          wsActiveRef.current = true;
          setMode('websocket');
          setError(null);
          void poll();
        };

        ws.onmessage = (event) => {
          if (cancelled || typeof event.data !== 'string') return;
          const parsed = parseWsMessage(event.data);
          if (parsed) {
            applyMetrics(parsed);
            setMode('websocket');
          }
        };

        ws.onerror = () => {
          if (cancelled) return;
          wsActiveRef.current = false;
          startPolling();
          setMode('polling');
        };

        ws.onclose = () => {
          if (cancelled) return;
          wsActiveRef.current = false;
          wsRef.current = null;
          startPolling();
          setMode('polling');
          reconnectTimer = setTimeout(connectWs, WS_RECONNECT_MS);
        };
      } catch {
        wsActiveRef.current = false;
        startPolling();
        setMode('polling');
        reconnectTimer = setTimeout(connectWs, WS_RECONNECT_MS);
      }
    };

    connectWs();
    startPolling();

    return () => {
      cancelled = true;
      wsActiveRef.current = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      stopPolling();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [applyMetrics, poll, storeId]);

  return { metrics, mode, error, lastUpdated };
}
