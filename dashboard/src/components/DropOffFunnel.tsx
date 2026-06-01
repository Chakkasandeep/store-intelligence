import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { FunnelStep } from '../types/api';

interface DropOffFunnelProps {
  steps: FunnelStep[];
  compact?: boolean;
}

const STAGE_COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7'];

export function DropOffFunnel({ steps, compact = false }: DropOffFunnelProps) {
  const data = steps.map((s, i) => ({
    stage: s.label ?? s.stage,
    count: s.count,
    dropOff: s.drop_off_pct ?? 0,
    fill: STAGE_COLORS[i % STAGE_COLORS.length],
  }));

  if (data.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-[var(--color-text-muted)]">
        Funnel data unavailable.
      </p>
    );
  }

  const height = compact ? 220 : 300;

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3a4f" horizontal={false} />
          <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey="stage"
            width={120}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#1a2332',
              border: '1px solid #2d3a4f',
              borderRadius: 8,
            }}
            formatter={(value, name) => {
              const num = typeof value === 'number' ? value : Number(value);
              if (name === 'dropOff') return [`${num.toFixed(1)}%`, 'Drop-off'];
              return [num, 'Sessions'];
            }}
          />
          <Bar dataKey="count" name="Sessions" radius={[0, 4, 4, 0]}>
            {data.map((entry) => (
              <Cell key={entry.stage} fill={entry.fill ?? '#3b82f6'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {!compact && (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {data.map((step) => (
            <div
              key={step.stage}
              className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
            >
              <span className="font-medium text-[var(--color-text)]">{step.stage}</span>
              <span className="ml-2 text-[var(--color-text-muted)]">
                {step.dropOff > 0 ? `−${step.dropOff.toFixed(1)}%` : 'entry'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
