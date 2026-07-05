import { GenericMetricDashboard } from '@/components/dashboard-client';

export default function Page() {
  return <GenericMetricDashboard title="Denúncias" description="Distribuição dos tipos de denúncia e evolução temporal quando a fonte oficial divulgar a série." endpoint="metrics" />;
}
