import type {
  Anomaly,
  HeatmapZone,
  StoreAnomalies,
  StoreFunnel,
  StoreHeatmap,
  StoreMetrics,
} from '../types/api';

/** Map backend FastAPI JSON → dashboard types */
export function normalizeMetrics(raw: Record<string, unknown>): StoreMetrics {
  const zoneVisits = (raw.zone_visits as Record<string, number> | undefined) ?? {};
  const top_zones = Object.entries(zoneVisits)
    .map(([zone_id, visits]) => ({
      zone_id,
      visits: Number(visits),
      avg_dwell_ms: 0,
    }))
    .sort((a, b) => b.visits - a.visits);

  const asOf = raw.as_of ?? raw.updated_at;

  return {
    store_id: String(raw.store_id ?? ''),
    current_visitors: Number(raw.current_visitors ?? 0),
    unique_visitors_today: Number(
      raw.unique_visitors_today ?? raw.unique_visitors ?? 0,
    ),
    conversion_rate: Number(raw.conversion_rate ?? 0),
    queue_depth: Number(raw.queue_depth ?? 0),
    abandonment_rate: Number(raw.abandonment_rate ?? 0),
    top_zones,
    updated_at: asOf ? String(asOf) : undefined,
  };
}

export function normalizeFunnel(raw: Record<string, unknown>): StoreFunnel {
  const stages = (raw.stages ?? raw.steps ?? []) as Array<Record<string, unknown>>;
  return {
    store_id: String(raw.store_id ?? ''),
    steps: stages.map((s) => ({
      stage: String(s.stage ?? ''),
      label: String(s.stage ?? ''),
      count: Number(s.visitors ?? s.count ?? 0),
      drop_off_pct: Number(s.drop_off_pct ?? 0),
    })),
  };
}

export function normalizeHeatmap(raw: Record<string, unknown>): StoreHeatmap {
  const zones = ((raw.zones ?? []) as Array<Record<string, unknown>>).map(
    (z): HeatmapZone => ({
      zone_id: String(z.zone_id ?? ''),
      visit_frequency: Number(z.visit_frequency ?? 0),
      avg_dwell: Number(z.avg_dwell_ms ?? z.avg_dwell ?? 0),
      row: z.row as number | undefined,
      col: z.col as number | undefined,
    }),
  );
  const conf = raw.data_confidence;
  const low =
    conf === 'LOW' || conf === false || conf === 'low';

  return {
    store_id: String(raw.store_id ?? ''),
    zones,
    data_confidence: !low,
    window_minutes: raw.window_minutes as number | undefined,
  };
}

export function normalizeAnomalies(raw: Record<string, unknown>): StoreAnomalies {
  const list = (raw.anomalies ?? []) as Array<Record<string, unknown>>;
  return {
    store_id: String(raw.store_id ?? ''),
    anomalies: list.map(
      (a): Anomaly => ({
        id: String(a.anomaly_id ?? a.id ?? ''),
        type: String(a.type ?? ''),
        severity: a.severity as Anomaly['severity'],
        message: String(a.root_cause ?? a.message ?? ''),
        suggested_action: String(a.suggested_action ?? ''),
        detected_at: a.detected_at ? String(a.detected_at) : undefined,
        zone_id: a.zone_id ? String(a.zone_id) : undefined,
      }),
    ),
  };
}

export function parseMetricsPayload(raw: string): StoreMetrics | null {
  try {
    const msg = JSON.parse(raw) as Record<string, unknown>;
    if (msg.payload && typeof msg.payload === 'object') {
      return normalizeMetrics(msg.payload as Record<string, unknown>);
    }
    if (msg.store_id && ('unique_visitors' in msg || 'unique_visitors_today' in msg)) {
      return normalizeMetrics(msg);
    }
  } catch {
    return null;
  }
  return null;
}
