import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ZoneMetric } from '../types/api';

interface TopZonesChartProps {
  zones: ZoneMetric[];
}

export function TopZonesChart({ zones }: TopZonesChartProps) {
  const data = [...zones]
    .sort((a, b) => b.visits - a.visits)
    .slice(0, 8)
    .map((z) => ({
      name: z.zone_id,
      visits: z.visits,
      dwellMin: z.avg_dwell_ms ? Math.round(z.avg_dwell_ms / 60_000) : 0,
    }));

  if (data.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-[var(--color-text-muted)]">
        No zone data yet for today.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3a4f" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
          axisLine={{ stroke: '#2d3a4f' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#94a3b8', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: '#1a2332',
            border: '1px solid #2d3a4f',
            borderRadius: 8,
          }}
          labelStyle={{ color: '#f1f5f9' }}
        />
        <Bar dataKey="visits" name="Visits" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
