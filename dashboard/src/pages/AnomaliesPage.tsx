import { useCallback } from 'react';
import { getStoreAnomalies } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import type { Anomaly, AnomalySeverity } from '../types/api';
import { usePollingResource } from '../hooks/usePollingResource';
import { formatRelativeTime } from '../utils/format';

const severityStyles: Record<AnomalySeverity, string> = {
  INFO: 'border-sky-500/40 bg-sky-500/10 text-sky-200',
  WARN: 'border-amber-500/40 bg-amber-500/10 text-amber-200',
  CRITICAL: 'border-red-500/40 bg-red-500/10 text-red-200',
};

function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  return (
    <article
      className={`rounded-xl border p-5 ${severityStyles[anomaly.severity]}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <span className="text-xs font-bold uppercase tracking-wide opacity-80">
            {anomaly.severity}
          </span>
          <h3 className="mt-1 text-base font-semibold text-[var(--color-text)]">
            {anomaly.type.replace(/_/g, ' ')}
          </h3>
        </div>
        {anomaly.detected_at && (
          <time className="text-xs text-[var(--color-text-muted)]">
            {formatRelativeTime(anomaly.detected_at)}
          </time>
        )}
      </div>
      <p className="mt-3 text-sm text-[var(--color-text)]">{anomaly.message}</p>
      {anomaly.zone_id && (
        <p className="mt-2 font-mono text-xs text-[var(--color-text-muted)]">
          Zone: {anomaly.zone_id}
        </p>
      )}
      <div className="mt-4 rounded-lg border border-white/10 bg-black/20 px-4 py-3">
        <p className="text-xs font-medium uppercase text-[var(--color-text-muted)]">
          Suggested action
        </p>
        <p className="mt-1 text-sm">{anomaly.suggested_action}</p>
      </div>
    </article>
  );
}

export function AnomaliesPage() {
  const fetchAnomalies = useCallback(() => getStoreAnomalies(), []);
  const { data, loading, error, lastUpdated } = usePollingResource(fetchAnomalies);
  const anomalies = data?.anomalies ?? [];

  const counts = anomalies.reduce(
    (acc, a) => {
      acc[a.severity] = (acc[a.severity] ?? 0) + 1;
      return acc;
    },
    {} as Record<AnomalySeverity, number>,
  );

  return (
    <>
      <PageHeader
        title="Anomalies"
        description="Active operational alerts: queue spikes, conversion drops, and dead zones."
        actions={
          lastUpdated ? (
            <span className="text-sm text-[var(--color-text-muted)]">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          ) : null
        }
      />
      <div className="space-y-6 p-8">
        <div className="flex flex-wrap gap-4">
          {(['CRITICAL', 'WARN', 'INFO'] as const).map((sev) => (
            <div
              key={sev}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-4 py-2 text-sm"
            >
              <span className="text-[var(--color-text-muted)]">{sev}</span>
              <span className="ml-2 font-semibold">{counts[sev] ?? 0}</span>
            </div>
          ))}
        </div>

        {loading && !data ? (
          <p className="py-16 text-center text-sm text-[var(--color-text-muted)]">
            Loading anomalies…
          </p>
        ) : anomalies.length === 0 ? (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-6 py-12 text-center">
            <p className="text-lg font-medium text-emerald-200">No active anomalies</p>
            <p className="mt-2 text-sm text-[var(--color-text-muted)]">
              Store operations look normal for the current window.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {anomalies.map((a) => (
              <AnomalyCard key={a.id} anomaly={a} />
            ))}
          </div>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
    </>
  );
}
