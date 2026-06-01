import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--color-border)] px-8 py-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-text)]">{title}</h2>
        {description && (
          <p className="mt-1 max-w-2xl text-sm text-[var(--color-text-muted)]">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  );
}
