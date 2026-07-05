import Link from 'next/link';
import type { ReactNode } from 'react';
import { ThemeToggle } from './theme-toggle';

const nav = [
  { href: '/', label: 'Home' },
  { href: '/comparison', label: 'Comparação' },
  { href: '/removals', label: 'Remoções' },
  { href: '/denuncias', label: 'Denúncias' },
  { href: '/seguranca-infantil', label: 'Segurança Infantil' },
  { href: '/ia', label: 'IA' },
  { href: '/transparencia', label: 'Transparência' },
  { href: '/lgpd', label: 'LGPD' },
  { href: '/eca', label: 'ECA Digital' },
];

export function SiteShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/70 backdrop-blur dark:border-slate-800 dark:bg-slate-950/70">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-4 lg:px-8">
          <div className="mr-auto">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">Social Platform Transparency Dashboard</p>
            <h1 className="text-lg font-bold tracking-tight text-slate-950 dark:text-white">Meta, TikTok e YouTube</h1>
          </div>
          <nav className="flex flex-wrap gap-2 text-sm">
            {nav.map((item) => (
              <Link key={item.href} href={item.href} className="rounded-full px-3 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white">
                {item.label}
              </Link>
            ))}
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 lg:px-8">{children}</main>
    </div>
  );
}
