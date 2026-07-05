import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';
import { SiteShell } from '@/components/site-shell';

export const metadata: Metadata = {
  title: 'Social Platform Transparency Dashboard',
  description: 'Comparativo oficial entre Meta, TikTok e YouTube sobre transparência, ECA Digital e LGPD.',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body>
        <SiteShell>{children}</SiteShell>
      </body>
    </html>
  );
}
