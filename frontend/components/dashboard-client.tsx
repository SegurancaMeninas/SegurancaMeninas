'use client';

import { useEffect, useMemo, useState } from 'react';
import { api, apiBaseUrl } from '@/lib/api';
import type { ComparisonRow, DashboardSummary, IndicatorReading, MetricReading, PlatformSummary, ReportSummary } from '@/lib/types';
import { KpiCard } from './kpi-card';
import { Card, CardDescription, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select } from './ui/select';
import { AreaTrendChart, PiePanel, RadarPanel, SimpleBarChart, TrendChart } from './charts';

const platformColors = { Meta: '#0ea5e9', TikTok: '#22c55e', YouTube: '#f59e0b' } as const;

function asNumber(value: string) {
  const numeric = Number(value.replace(/[^0-9.,-]/g, '').replace(',', '.'));
  return Number.isFinite(numeric) ? numeric : 0;
}

function emptyStateText(value?: string | null) {
  return value ? value : 'Não divulgado oficialmente.';
}

export function HomeDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [metrics, setMetrics] = useState<MetricReading[]>([]);
  const [indicators, setIndicators] = useState<IndicatorReading[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.summary(), api.reports(), api.metrics(), api.indicators()])
      .then(([summaryData, reportsData, metricsData, indicatorData]) => {
        setSummary(summaryData);
        setReports(reportsData);
        setMetrics(metricsData);
        setIndicators(indicatorData);
      })
      .finally(() => setLoading(false));
  }, []);

  const lastUpdate = summary?.last_update ? new Date(summary.last_update).toLocaleString('pt-BR') : 'Sem coletas ainda';
  const platformCards: PlatformSummary[] = summary?.platform_cards ?? [];
  const chartData = useMemo(() => {
    return platformCards.map((card: PlatformSummary) => ({
      platform: card.platform,
      reports: card.report_count,
      metrics: card.metric_count,
      transparency: card.score_transparency || 0,
    }));
  }, [platformCards]);

  return (
    <section className="grid gap-8">
      <div className="grid gap-6 rounded-[2rem] border border-slate-200/80 bg-gradient-to-br from-sky-50 via-white to-amber-50 p-8 shadow-glow dark:border-slate-800 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900 lg:grid-cols-[1.3fr_0.7fr]">
        <div>
          <Badge className="mb-4 bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">Fontes oficiais בלבד</Badge>
          <h2 className="max-w-3xl text-4xl font-extrabold tracking-tight text-slate-950 dark:text-white">Comparação automatizada de transparência, LGPD e ECA Digital usando apenas relatórios oficiais.</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
            O painel organiza Meta, TikTok e YouTube em um fluxo único de ingestão, armazenamento e visualização. Quando uma métrica não aparece na fonte oficial, a interface mostra exatamente: Não divulgado oficialmente.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button onClick={async () => {
              await api.refresh();
              window.location.reload();
            }}>Atualizar agora</Button>
            <a className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-950 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white" href={`${apiBaseUrl}/export/pdf`} target="_blank" rel="noreferrer">Exportar PDF</a>
            <a className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-950 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white" href={`${apiBaseUrl}/export/excel`} target="_blank" rel="noreferrer">Exportar Excel</a>
            <a className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-950 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-white" href={`${apiBaseUrl}/export/csv`} target="_blank" rel="noreferrer">Exportar CSV</a>
          </div>
        </div>
        <Card className="bg-white/70 dark:bg-slate-950/60">
          <CardDescription>Última atualização</CardDescription>
          <CardTitle className="mt-2 text-2xl">{lastUpdate}</CardTitle>
          <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
              <p className="text-slate-500">Métricas</p>
              <p className="mt-1 text-2xl font-bold">{summary?.metric_count ?? 0}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
              <p className="text-slate-500">Relatórios</p>
              <p className="mt-1 text-2xl font-bold">{summary?.report_count ?? 0}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
              <p className="text-slate-500">Plataformas</p>
              <p className="mt-1 text-2xl font-bold">3</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
              <p className="text-slate-500">Status</p>
              <p className="mt-1 text-2xl font-bold">{loading ? 'Carregando' : 'Pronto'}</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Métricas totais" value={String(summary?.metric_count ?? 0)} hint="Campos oficiais armazenados" />
        <KpiCard label="Relatórios coletados" value={String(summary?.report_count ?? 0)} hint="Fontes rastreadas a partir dos centros oficiais" />
        <KpiCard label="Valores divulgados" value={String(metrics.length)} hint="Linhas de métricas recuperadas" />
        <KpiCard label="Índices calculados" value={String(indicators.length)} hint="Transparência, LGPD e ECA" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <Card>
          <CardHeaderText title="Comparativo rápido" description="Visão geral do volume de dados por plataforma." />
          <SimpleBarChart data={chartData} xKey="platform" yKey="reports" />
        </Card>
        <Card>
          <CardHeaderText title="Distribuição de plataforma" description="Quantidade de relatórios por plataforma." />
          <PiePanel data={chartData.map((item) => ({ name: item.platform, value: item.reports }))} nameKey="name" valueKey="value" />
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeaderText title="Indicadores" description="Pontuações calculadas a partir de dados oficiais ou ausência de divulgação." />
          <div className="grid gap-4 md:grid-cols-2">
            {indicators.map((indicator) => (
              <div key={indicator.code} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                <p className="text-sm text-slate-500">{indicator.name}</p>
                <p className="mt-2 text-2xl font-bold">{indicator.score === null ? 'Não divulgado oficialmente.' : indicator.score.toFixed(2)}</p>
                <p className="mt-2 text-xs text-slate-500">{indicator.notes}</p>
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <CardHeaderText title="Relatórios recentes" description="Lista de publicações encontradas." />
          <div className="space-y-3">
            {reports.slice(0, 6).map((report) => (
              <div key={report.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                <p className="text-sm font-semibold">{report.platform}</p>
                <p className="text-sm text-slate-500">{report.title}</p>
              </div>
            ))}
            {!reports.length ? <p className="text-sm text-slate-500">Nenhum relatório coletado ainda.</p> : null}
          </div>
        </Card>
      </div>
    </section>
  );
}

export function ComparisonDashboard() {
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [platform, setPlatform] = useState('');
  const [year, setYear] = useState('');
  const [quarter, setQuarter] = useState('');

  useEffect(() => {
    api.comparison({ platform: platform || undefined, year: year ? Number(year) : undefined, quarter: quarter ? Number(quarter) : undefined }).then(setRows);
  }, [platform, year, quarter]);

  return (
    <section className="space-y-6">
      <Card>
        <CardHeaderText title="Filtros" description="Ano, trimestre e plataforma." />
        <div className="grid gap-4 md:grid-cols-3">
          <Select value={platform} onChange={(event) => setPlatform(event.target.value)}>
            <option value="">Todas as plataformas</option>
            <option value="meta">Meta</option>
            <option value="tiktok">TikTok</option>
            <option value="youtube">YouTube</option>
          </Select>
          <Input value={year} onChange={(event) => setYear(event.target.value)} placeholder="Ano" />
          <Input value={quarter} onChange={(event) => setQuarter(event.target.value)} placeholder="Trimestre" />
        </div>
      </Card>
      <Card>
        <CardHeaderText title="Tabela comparativa" description="Somente dados extraídos de fontes oficiais." />
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="px-3 py-2">Plataforma</th>
                <th className="px-3 py-2">Métrica</th>
                <th className="px-3 py-2">Valor</th>
                <th className="px-3 py-2">Fonte</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index} className="border-t border-slate-200 dark:border-slate-800">
                  <td className="px-3 py-3 font-medium">{row.platform}</td>
                  <td className="px-3 py-3">{row.metric}</td>
                  <td className="px-3 py-3">{emptyStateText(row.value)}</td>
                  <td className="px-3 py-3 text-cyan-600 dark:text-cyan-400">{row.source_url}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}

export function GenericMetricDashboard({ title, description, endpoint }: { title: string; description: string; endpoint: 'metrics' | 'reports' | 'indicators' }) {
  const [metrics, setMetrics] = useState<MetricReading[]>([]);
  const [indicators, setIndicators] = useState<IndicatorReading[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);

  useEffect(() => {
    if (endpoint === 'metrics') api.metrics().then(setMetrics);
    if (endpoint === 'indicators') api.indicators().then(setIndicators);
    if (endpoint === 'reports') api.reports().then(setReports);
  }, [endpoint]);

  return (
    <section className="space-y-6">
      <Card>
        <CardHeaderText title={title} description={description} />
      </Card>
      {endpoint === 'metrics' ? <MetricCharts metrics={metrics} /> : null}
      {endpoint === 'indicators' ? <IndicatorCharts indicators={indicators} /> : null}
      {endpoint === 'reports' ? <ReportsList reports={reports} /> : null}
    </section>
  );
}

function MetricCharts({ metrics }: { metrics: MetricReading[] }) {
  const grouped = metrics.reduce<Record<string, number>>((accumulator, metric) => {
    accumulator[metric.category] = (accumulator[metric.category] || 0) + 1;
    return accumulator;
  }, {});
  const data = Object.entries(grouped).map(([name, value]) => ({ name, value }));
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Card>
        <CardHeaderText title="Categorias extraídas" description="Agrupamento das métricas por categoria." />
        <PiePanel data={data} nameKey="name" valueKey="value" />
      </Card>
      <Card>
        <CardHeaderText title="Volume de métricas" description="Total por categoria." />
        <SimpleBarChart data={data} xKey="name" yKey="value" />
      </Card>
    </div>
  );
}

function IndicatorCharts({ indicators }: { indicators: IndicatorReading[] }) {
  const data = indicators.map((indicator) => ({ subject: indicator.name, score: indicator.score ?? 0 }));
  return (
    <Card>
      <CardHeaderText title="Radar dos indicadores" description="Visão comparativa dos índices calculados." />
      <RadarPanel data={data} keys={["score"]} />
    </Card>
  );
}

function ReportsList({ reports }: { reports: ReportSummary[] }) {
  return (
    <Card>
      <CardHeaderText title="Relatórios" description="Catálogo de fontes oficiais armazenadas." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {reports.map((report) => (
          <div key={report.id} className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
            <p className="text-sm font-semibold">{report.platform}</p>
            <p className="text-sm text-slate-500">{report.title}</p>
            <a className="mt-3 inline-block text-sm text-cyan-600 dark:text-cyan-400" href={report.reference_url} target="_blank" rel="noreferrer">Abrir fonte oficial</a>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CardHeaderText({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">{title}</h2>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
    </div>
  );
}
