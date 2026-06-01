export type AnomalySeverity = 'INFO' | 'WARN' | 'CRITICAL';

export interface ZoneMetric {
  zone_id: string;
  visits: number;
  avg_dwell_ms?: number;
}

export interface StoreMetrics {
  store_id: string;
  current_visitors: number;
  unique_visitors_today: number;
  conversion_rate: number;
  queue_depth: number;
  abandonment_rate?: number;
  avg_dwell_by_zone?: Record<string, number>;
  top_zones?: ZoneMetric[];
  updated_at?: string;
}

export interface FunnelStep {
  stage: string;
  label?: string;
  count: number;
  drop_off_pct?: number;
}

export interface StoreFunnel {
  store_id: string;
  steps: FunnelStep[];
}

export interface HeatmapZone {
  zone_id: string;
  visit_frequency: number;
  avg_dwell: number;
  row?: number;
  col?: number;
}

export interface StoreHeatmap {
  store_id: string;
  zones: HeatmapZone[];
  data_confidence?: boolean;
  window_minutes?: number;
}

export interface Anomaly {
  id: string;
  type: string;
  severity: AnomalySeverity;
  message: string;
  suggested_action: string;
  detected_at?: string;
  zone_id?: string;
}

export interface StoreAnomalies {
  store_id: string;
  anomalies: Anomaly[];
}

export interface StoreHealthEntry {
  store_id: string;
  last_event_at?: string | null;
  stale_feed?: boolean;
  lag_seconds?: number;
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'down' | string;
  stores?: StoreHealthEntry[];
  warnings?: string[];
  uptime_seconds?: number;
}

export interface WsMetricsMessage {
  type: 'metrics' | 'ping' | 'pong';
  store_id?: string;
  payload?: StoreMetrics;
  timestamp?: string;
}
