import type { ConnectionMode } from '../hooks/useLiveMetrics';

interface ConnectionStatusProps {
  mode: ConnectionMode;
  lastUpdated: Date | null;
  error: string | null;
}

const labels: Record<ConnectionMode, string> = {
  websocket: 'Live (WebSocket)',
  polling: 'Polling (10s)',
  connecting: 'Connecting…',
  offline: 'Offline',
};

const dotClass: Record<ConnectionMode, string> = {
  websocket: 'bg-emerald-400 shadow-emerald-400/50',
  polling: 'bg-amber-400 shadow-amber-400/50',
  connecting: 'bg-sky-400 animate-pulse',
  offline: 'bg-red-400',
};

export function ConnectionStatus({ mode, lastUpdated, error }: ConnectionStatusProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--color-text-muted)]">
      <span className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-1">
        <span className={`h-2 w-2 rounded-full shadow-sm ${dotClass[mode]}`} />
        {labels[mode]}
      </span>
      {lastUpdated && (
        <span>Updated {lastUpdated.toLocaleTimeString()}</span>
      )}
      {error && <span className="text-red-400">{error}</span>}
    </div>
  );
}
