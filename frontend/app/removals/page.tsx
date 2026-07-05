import { GenericMetricDashboard } from '@/components/dashboard-client';

export default function Page() {
  return <GenericMetricDashboard title="Remoções" description="Gráficos de remoções, séries temporais e distribuição por plataforma." endpoint="metrics" />;
}
