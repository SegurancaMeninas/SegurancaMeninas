import type { ComparisonRow, DashboardSummary, IndicatorReading, MetricReading, RefreshResponse, ReportSummary } from './types';

export const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  summary: () => request<DashboardSummary>('/dashboard/summary'),
  metrics: (platform?: string) => request<MetricReading[]>(platform ? `/metrics?platform=${encodeURIComponent(platform)}` : '/metrics'),
  reports: () => request<ReportSummary[]>('/reports'),
  indicators: () => request<IndicatorReading[]>('/indicators'),
  comparison: (params?: { platform?: string; year?: number; quarter?: number }) => {
    const search = new URLSearchParams();
    if (params?.platform) search.set('platform', params.platform);
    if (params?.year) search.set('year', String(params.year));
    if (params?.quarter) search.set('quarter', String(params.quarter));
    return request<ComparisonRow[]>(`/comparison${search.toString() ? `?${search.toString()}` : ''}`);
  },
  refresh: () => request<RefreshResponse>('/refresh'),
};
