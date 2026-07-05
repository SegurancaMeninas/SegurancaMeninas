import { Card, CardDescription, CardTitle } from '@/components/ui/card';

export function KpiCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card className="bg-gradient-to-br from-sky-50 via-white to-amber-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900">
      <CardDescription>{label}</CardDescription>
      <CardTitle className="mt-2 text-3xl">{value}</CardTitle>
      {hint ? <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{hint}</p> : null}
    </Card>
  );
}
