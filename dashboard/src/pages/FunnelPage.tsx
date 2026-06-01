import { useCallback } from 'react';
import { getStoreFunnel } from '../api/client';
import { DropOffFunnel } from '../components/DropOffFunnel';
import { PageHeader } from '../components/PageHeader';
import { Panel } from '../components/Panel';
import { usePollingResource } from '../hooks/usePollingResource';
import { formatNumber, formatPercent } from '../utils/format';

export function FunnelPage() {
  const fetchFunnel = useCallback(() => getStoreFunnel(), []);
  const { data, loading, error, lastUpdated } = usePollingResource(fetchFunnel);
  const steps = data?.steps ?? [];

  const entryCount = steps[0]?.count ?? 0;
  const finalCount = steps.length > 0 ? (steps[steps.length - 1]?.count ?? 0) : 0;
  const overallConversion =
    entryCount > 0 ? (finalCount / entryCount) * 100 : undefined;

  return (
    <>
      <PageHeader
        title="Conversion Funnel"
        description="Session-level funnel: Entry → Zone Visit → Billing Queue → Purchase. Re-entries are not double-counted."
        actions={
          lastUpdated ? (
            <span className="text-sm text-[var(--color-text-muted)]">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          ) : null
        }
      />
      <div className="space-y-6 p-8">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <p className="text-sm text-[var(--color-text-muted)]">Sessions entered</p>
            <p className="mt-2 text-2xl font-semibold">{formatNumber(entryCount)}</p>
          </div>
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <p className="text-sm text-[var(--color-text-muted)]">Completed purchase</p>
            <p className="mt-2 text-2xl font-semibold">{formatNumber(finalCount)}</p>
          </div>
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
            <p className="text-sm text-[var(--color-text-muted)]">End-to-end conversion</p>
            <p className="mt-2 text-2xl font-semibold">{formatPercent(overallConversion)}</p>
          </div>
        </div>

        <Panel title="Drop-off by stage" subtitle="Counts and drop-off percentage between stages">
          {loading && !data ? (
            <p className="py-16 text-center text-sm text-[var(--color-text-muted)]">
              Loading funnel data…
            </p>
          ) : (
            <DropOffFunnel steps={steps} />
          )}
          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </Panel>

        {steps.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-[var(--color-border)]">
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--color-surface-raised)] text-[var(--color-text-muted)]">
                <tr>
                  <th className="px-5 py-3 font-medium">Stage</th>
                  <th className="px-5 py-3 font-medium">Sessions</th>
                  <th className="px-5 py-3 font-medium">Drop-off vs prior</th>
                </tr>
              </thead>
              <tbody>
                {steps.map((step) => (
                  <tr key={step.stage} className="border-t border-[var(--color-border)]">
                    <td className="px-5 py-3 font-medium">{step.label ?? step.stage}</td>
                    <td className="px-5 py-3 font-mono">{formatNumber(step.count)}</td>
                    <td className="px-5 py-3 font-mono">
                      {step.drop_off_pct !== undefined
                        ? formatPercent(step.drop_off_pct)
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
