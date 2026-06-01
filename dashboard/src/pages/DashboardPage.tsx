import { useCallback } from 'react';
import { getStoreFunnel } from '../api/client';
import { ConnectionStatus } from '../components/ConnectionStatus';
import { DropOffFunnel } from '../components/DropOffFunnel';
import { PageHeader } from '../components/PageHeader';
import { Panel } from '../components/Panel';
import { StatCard } from '../components/StatCard';
import { TopZonesChart } from '../components/TopZonesChart';
import { useLiveMetrics } from '../hooks/useLiveMetrics';
import { usePollingResource } from '../hooks/usePollingResource';
import { formatNumber, formatPercent } from '../utils/format';

export function DashboardPage() {
  const { metrics, mode, error, lastUpdated } = useLiveMetrics();
  const fetchFunnel = useCallback(() => getStoreFunnel(), []);
  const funnelState = usePollingResource(fetchFunnel);

  const topZones =
    metrics?.top_zones ??
    (metrics?.avg_dwell_by_zone
      ? Object.entries(metrics.avg_dwell_by_zone).map(([zone_id, avg_dwell_ms]) => ({
          zone_id,
          visits: 0,
          avg_dwell_ms,
        }))
      : []);

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Live store metrics — WebSocket with 10s polling fallback."
        actions={
          <ConnectionStatus mode={mode} lastUpdated={lastUpdated} error={error} />
        }
      />
      <div className="space-y-6 p-8">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Current Visitors"
            value={formatNumber(metrics?.current_visitors)}
            subtitle="In store now"
            accent="blue"
          />
          <StatCard
            title="Today's Visitors"
            value={formatNumber(metrics?.unique_visitors_today)}
            subtitle="Unique customers (staff excluded)"
            accent="green"
          />
          <StatCard
            title="Conversion Rate"
            value={formatPercent(metrics?.conversion_rate)}
            subtitle={
              metrics?.abandonment_rate !== undefined
                ? `Abandonment ${formatPercent(metrics.abandonment_rate)}`
                : 'Session → purchase'
            }
            accent="violet"
          />
          <StatCard
            title="Queue Depth"
            value={formatNumber(metrics?.queue_depth)}
            subtitle="Billing queue"
            accent="amber"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Panel title="Top Zones" subtitle="Visit volume by zone today">
            <TopZonesChart zones={topZones} />
          </Panel>
          <Panel title="Drop-off Funnel" subtitle="Entry → zone → billing → purchase">
            {funnelState.loading && !funnelState.data ? (
              <p className="py-12 text-center text-sm text-[var(--color-text-muted)]">
                Loading funnel…
              </p>
            ) : (
              <DropOffFunnel steps={funnelState.data?.steps ?? []} compact />
            )}
            {funnelState.error && (
              <p className="mt-2 text-sm text-red-400">{funnelState.error}</p>
            )}
          </Panel>
        </div>
      </div>
    </>
  );
}
