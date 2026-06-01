import { useCallback } from 'react';
import { getStoreHeatmap } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import { Panel } from '../components/Panel';
import { ZoneHeatmapGrid } from '../components/ZoneHeatmapGrid';
import { usePollingResource } from '../hooks/usePollingResource';

export function HeatmapPage() {
  const fetchHeatmap = useCallback(() => getStoreHeatmap(), []);
  const { data, loading, error, lastUpdated, refresh } = usePollingResource(fetchHeatmap);

  return (
    <>
      <PageHeader
        title="Zone Heatmap"
        description="Visit frequency and dwell intensity normalized 0–100. Refreshes every 10 seconds."
        actions={
          <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
            {lastUpdated && <span>Updated {lastUpdated.toLocaleTimeString()}</span>}
            <button
              type="button"
              onClick={refresh}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1.5 text-sm text-[var(--color-text)] hover:bg-[var(--color-surface-overlay)]"
            >
              Refresh
            </button>
          </div>
        }
      />
      <div className="p-8">
        <Panel
          title="Store floor heatmap"
          subtitle={
            data?.window_minutes
              ? `Rolling ${data.window_minutes} minute window`
              : 'Zone visit frequency + average dwell'
          }
        >
          {loading && !data ? (
            <p className="py-16 text-center text-sm text-[var(--color-text-muted)]">
              Loading heatmap…
            </p>
          ) : (
            <ZoneHeatmapGrid
              zones={data?.zones ?? []}
              lowConfidence={data?.data_confidence === false}
            />
          )}
          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </Panel>
        <div className="mt-6 flex flex-wrap gap-4 text-xs text-[var(--color-text-muted)]">
          <span className="flex items-center gap-2">
            <span className="h-3 w-8 rounded bg-slate-600/50" /> Low
          </span>
          <span className="flex items-center gap-2">
            <span className="h-3 w-8 rounded bg-sky-500/60" /> Medium
          </span>
          <span className="flex items-center gap-2">
            <span className="h-3 w-8 rounded bg-amber-500/70" /> High
          </span>
          <span className="flex items-center gap-2">
            <span className="h-3 w-8 rounded bg-red-500/90" /> Peak
          </span>
        </div>
      </div>
    </>
  );
}
