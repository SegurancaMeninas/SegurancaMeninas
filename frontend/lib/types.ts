export type PlatformSummary = {
  platform: string;
  last_update: string | null;
  metric_count: number;
  report_count: number;
  score_transparency: number | null;
  score_lgpd: number | null;
  score_eca: number | null;
};

export type DashboardSummary = {
  last_update: string | null;
  metric_count: number;
  report_count: number;
  platform_cards: PlatformSummary[];
};

export type MetricReading = {
  platform: string;
  metric_code: string;
  metric_name: string;
  category: string;
  value: string;
  source_url: string;
  report_period_label: string | null;
  disclosure_status: string;
};

export type ComparisonRow = {
  platform: string;
  quarter: string | null;
  year: number | null;
  metric: string;
  value: string;
  source_url: string;
  report_date: string | null;
  report_period_label: string | null;
};

export type IndicatorReading = {
  code: string;
  name: string;
  score: number | null;
  notes: string | null;
};

export type ReportSummary = {
  id: number;
  platform: string;
  title: string;
  report_type: string;
  reference_url: string;
  report_period_label: string | null;
  published_at: string | null;
};

export type RefreshResponse = {
  processed: number;
  reports: number;
  metric_values: number;
  sources: Array<Record<string, unknown>>;
  errors: Array<Record<string, unknown>>;
};
