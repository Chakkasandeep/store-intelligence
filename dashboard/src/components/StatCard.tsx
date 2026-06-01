interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  accent?: 'blue' | 'green' | 'amber' | 'violet';
}

const accentRing: Record<NonNullable<StatCardProps['accent']>, string> = {
  blue: 'from-blue-500/20 to-transparent',
  green: 'from-emerald-500/20 to-transparent',
  amber: 'from-amber-500/20 to-transparent',
  violet: 'from-violet-500/20 to-transparent',
};

export function StatCard({
  title,
  value,
  subtitle,
  trend = 'neutral',
  accent = 'blue',
}: StatCardProps) {
  const trendColor =
    trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-[var(--color-text-muted)]';

  return (
    <article className="relative overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] p-5">
      <div
        className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${accentRing[accent]} opacity-80`}
      />
      <div className="relative">
        <p className="text-sm font-medium text-[var(--color-text-muted)]">{title}</p>
        <p className="mt-2 text-3xl font-semibold tracking-tight text-[var(--color-text)]">
          {value}
        </p>
        {subtitle && <p className={`mt-1 text-sm ${trendColor}`}>{subtitle}</p>}
      </div>
    </article>
  );
}
