import type { HeatmapZone } from '../types/api';

interface ZoneHeatmapGridProps {
  zones: HeatmapZone[];
  lowConfidence?: boolean;
}

function intensityColor(value: number): string {
  if (value >= 80) return 'bg-red-500/90';
  if (value >= 60) return 'bg-orange-500/80';
  if (value >= 40) return 'bg-amber-500/70';
  if (value >= 20) return 'bg-sky-500/60';
  return 'bg-slate-600/50';
}

export function ZoneHeatmapGrid({ zones, lowConfidence }: ZoneHeatmapGridProps) {
  if (zones.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-[var(--color-text-muted)]">
        No heatmap zones returned for this store.
      </p>
    );
  }

  const hasGrid = zones.some((z) => z.row !== undefined && z.col !== undefined);

  if (hasGrid) {
    const maxRow = Math.max(...zones.map((z) => z.row ?? 0));
    const maxCol = Math.max(...zones.map((z) => z.col ?? 0));
    const grid: (HeatmapZone | null)[][] = Array.from({ length: maxRow + 1 }, () =>
      Array.from({ length: maxCol + 1 }, () => null),
    );
    for (const zone of zones) {
      const r = zone.row ?? 0;
      const c = zone.col ?? 0;
      const row = grid[r];
      if (row) row[c] = zone;
    }

    return (
      <div className="space-y-4">
        {lowConfidence && (
          <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
            Low data confidence — fewer than 20 sessions in the analysis window.
          </p>
        )}
        <div
          className="inline-grid gap-2"
          style={{
            gridTemplateColumns: `repeat(${maxCol + 1}, minmax(5rem, 1fr))`,
          }}
        >
          {grid.flatMap((row, ri) =>
            row.map((cell, ci) => {
              if (!cell) {
                return (
                  <div
                    key={`empty-${ri}-${ci}`}
                    className="flex h-20 items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] text-xs text-[var(--color-text-muted)]"
                  >
                    —
                  </div>
                );
              }
              const score = Math.round((cell.visit_frequency + cell.avg_dwell) / 2);
              return (
                <div
                  key={cell.zone_id}
                  className={`flex h-20 flex-col items-center justify-center rounded-lg border border-[var(--color-border)] ${intensityColor(score)}`}
                  title={`Visit: ${cell.visit_frequency}, Dwell: ${cell.avg_dwell}`}
                >
                  <span className="text-xs font-semibold text-white">{cell.zone_id}</span>
                  <span className="text-[10px] text-white/80">{score}</span>
                </div>
              );
            }),
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {lowConfidence && (
        <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200">
          Low data confidence — fewer than 20 sessions in the analysis window.
        </p>
      )}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {zones.map((zone) => {
          const score = Math.round((zone.visit_frequency + zone.avg_dwell) / 2);
          return (
            <div
              key={zone.zone_id}
              className={`rounded-lg border border-[var(--color-border)] p-4 ${intensityColor(score)}`}
            >
              <p className="font-semibold text-white">{zone.zone_id}</p>
              <dl className="mt-2 grid grid-cols-2 gap-2 text-xs text-white/90">
                <div>
                  <dt className="opacity-70">Visits</dt>
                  <dd className="font-mono">{zone.visit_frequency}</dd>
                </div>
                <div>
                  <dt className="opacity-70">Dwell</dt>
                  <dd className="font-mono">{zone.avg_dwell}</dd>
                </div>
              </dl>
            </div>
          );
        })}
      </div>
    </div>
  );
}
