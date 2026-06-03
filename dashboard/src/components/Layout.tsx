import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { getSelectedStoreId, setSelectedStoreId } from '../config';
import { getHealth } from '../api/client';

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/heatmap', label: 'Heatmap' },
  { to: '/funnel', label: 'Funnel' },
  { to: '/anomalies', label: 'Anomalies' },
  { to: '/health', label: 'System Health' },
] as const;

export function Layout() {
  const [currentStore, setCurrentStore] = useState(getSelectedStoreId());
  const [availableStores, setAvailableStores] = useState<string[]>(['ST1008', 'ST_STORE2']);

  useEffect(() => {
    getHealth()
      .then((data) => {
        if (data && data.stores) {
          const ids = data.stores.map((s) => s.store_id);
          if (ids.length > 0) {
            setAvailableStores(ids);
          }
        }
      })
      .catch((err) => {
        console.warn('Failed to load active stores list from health endpoint, using defaults:', err);
      });
  }, []);

  const handleStoreChange = (storeId: string) => {
    setSelectedStoreId(storeId);
    setCurrentStore(storeId);
    // Reload the page to reset websockets and fetch new metrics
    window.location.reload();
  };

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface-raised)]">
        <div className="border-b border-[var(--color-border)] px-5 py-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            Store Intelligence
          </p>
          <h1 className="mt-1 text-lg font-semibold text-[var(--color-text)]">Apex Retail</h1>
          
          <div className="mt-4">
            <label htmlFor="store-selector" className="sr-only">Select Store</label>
            <select
              id="store-selector"
              value={currentStore}
              onChange={(e) => handleStoreChange(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface-overlay)] px-2 py-1.5 font-sans text-sm text-[var(--color-text)] outline-none focus:border-sky-400"
            >
              {availableStores.map((id) => (
                <option key={id} value={id}>
                  {id === 'ST1008' ? 'ST1008 (Brigade)' : id === 'ST_STORE2' ? 'ST_STORE2 (Store 2)' : id}
                </option>
              ))}
            </select>
          </div>
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
