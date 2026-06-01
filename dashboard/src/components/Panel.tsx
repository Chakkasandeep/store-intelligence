import type { ReactNode } from 'react';

interface PanelProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, subtitle, children, className = '' }: PanelProps) {
  return (
    <section
      className={`rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-raised)] ${className}`}
    >
      <div className="border-b border-[var(--color-border)] px-5 py-4">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">{title}</h3>
        {subtitle && (
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{subtitle}</p>
        )}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}
