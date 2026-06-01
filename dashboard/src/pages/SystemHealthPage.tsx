import { useCallback } from 'react';
import { getHealth } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import { Panel } from '../components/Panel';
import { STORE_ID } from '../config';
import { usePollingResource } from '../hooks/usePollingResource';
import { formatRelativeTime } from '../utils/format';

function statusBadge(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized === 'ok') return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
  if (normalized === 'degraded') return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
  return 'bg-red-500/20 text-red-300 border-red-500/40';
}

export function SystemHealthPage() {
  const fetchHealth = useCallback(() => getHealth(), []);
  const { data, loading, error, lastUpdated } = usePollingResource(fetchHealth);

  const currentStore = data?.stores?.find((s) => s.store_id === STORE_ID);

  return (
    <>
      <PageHeader
        title="System Health"
        description="Service status, per-store feed freshness, and STALE_FEED warnings (>10 min lag)."
        actions={
          lastUpdated ? (
            <span className="text-sm text-[var(--color-text-muted)]">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          ) : null
        }
      />
      <div className="space-y-6 p-8">
        {loading && !data ? (
          <p className="py-16 text-center text-sm text-[var(--color-text-muted)]">
            Loading health status…
          </p>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Panel title="API status">
                <span
                  className={`inline-flex rounded-full border px-3 py-1 text-sm font-semibold uppercase ${statusBadge(data?.status ?? 'unknown')}`}
                >
                  {data?.status ?? 'unknown'}
                </span>
                {data?.uptime_seconds !== undefined && (
                  <p className="mt-4 text-sm text-[var(--color-text-muted)]">
                    Uptime: {Math.floor(data.uptime_seconds / 3600)}h{' '}
                    {Math.floor((data.uptime_seconds % 3600) / 60)}m
                  </p>
                )}
              </Panel>

              <Panel title={`Store ${STORE_ID}`}>
                {currentStore ? (
                  <dl className="space-y-3 text-sm">
                    <div>
                      <dt className="text-[var(--color-text-muted)]">Last event</dt>
                      <dd className="mt-0.5 font-mono">
                        {formatRelativeTime(currentStore.last_event_at)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--color-text-muted)]">Feed status</dt>
                      <dd className="mt-0.5">
                        {currentStore.stale_feed ? (
                          <span className="font-semibold text-amber-400">STALE_FEED</span>
                        ) : (
                          <span className="text-emerald-400">Fresh</span>
                        )}
                      </dd>
                    </div>
                    {currentStore.lag_seconds !== undefined && (
                      <div>
                        <dt className="text-[var(--color-text-muted)]">Lag</dt>
                        <dd className="mt-0.5 font-mono">{currentStore.lag_seconds}s</dd>
                      </div>
                    )}
                  </dl>
                ) : (
                  <p className="text-sm text-[var(--color-text-muted)]">
                    No health entry for this store in the response.
                  </p>
                )}
              </Panel>

              <Panel title="Warnings">
                {data?.warnings && data.warnings.length > 0 ? (
                  <ul className="space-y-2 text-sm text-amber-200">
                    {data.warnings.map((w) => (
                      <li key={w} className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                        {w}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-[var(--color-text-muted)]">No active warnings.</p>
                )}
              </Panel>
            </div>

            {data?.stores && data.stores.length > 0 && (
              <div className="overflow-hidden rounded-xl border border-[var(--color-border)]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]">
                    <tr>
                      <th className="px-5 py-3 font-medium">Store</th>
                      <th className="px-5 py-3 font-medium">Last event</th>
                      <th className="px-5 py-3 font-medium">Stale</th>
                      <th className="px-5 py-3 font-medium">Lag (s)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.stores.map((store) => (
                      <tr
                        key={store.store_id}
                        className={`border-t border-[var(--color-border)] ${
                          store.store_id === STORE_ID ? 'bg-sky-500/5' : ''
                        }`}
                      >
                        <td className="px-5 py-3 font-mono">{store.store_id}</td>
                        <td className="px-5 py-3">
                          {formatRelativeTime(store.last_event_at)}
                        </td>
                        <td className="px-5 py-3">
                          {store.stale_feed ? (
                            <span className="text-amber-400">Yes</span>
                          ) : (
                            <span className="text-emerald-400">No</span>
                          )}
                        </td>
                        <td className="px-5 py-3 font-mono">
                          {store.lag_seconds ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
      </div>
    </>
  );
}
