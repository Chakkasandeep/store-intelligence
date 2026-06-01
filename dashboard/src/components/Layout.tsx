import { NavLink, Outlet } from 'react-router-dom';
import { STORE_ID } from '../config';

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/heatmap', label: 'Heatmap' },
  { to: '/funnel', label: 'Funnel' },
  { to: '/anomalies', label: 'Anomalies' },
  { to: '/health', label: 'System Health' },
] as const;

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface-raised)]">
        <div className="border-b border-[var(--color-border)] px-5 py-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            Store Intelligence
          </p>
          <h1 className="mt-1 text-lg font-semibold text-[var(--color-text)]">Apex Retail</h1>
          <p className="mt-2 font-mono text-xs text-sky-400">{STORE_ID}</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={'end' in item ? item.end : false}
              className={({ isActive }) =>
                [
                  'rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-[var(--color-accent-muted)] text-sky-300'
                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-overlay)] hover:text-[var(--color-text)]',
                ].join(' ')
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  );
}
