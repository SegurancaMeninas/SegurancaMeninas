from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MetricDefinition:
    code: str
    name: str
    category: str
    official_label: str | None = None
    description: str | None = None
    unit: str = "text"
    is_boolean: bool = False
    synonyms: tuple[str, ...] = ()


METRIC_DEFINITIONS: list[MetricDefinition] = [
    MetricDefinition("content_removed_total", "Número de conteúdos removidos", "Remoção de Conteúdo", "content removed", unit="number", synonyms=("removed content", "content removed", "removals")),
    MetricDefinition("content_removed_automatic", "Conteúdo removido automaticamente", "Remoção de Conteúdo", unit="number", synonyms=("automatically removed", "automated removals", "auto removals")),
    MetricDefinition("content_removed_after_report", "Conteúdo removido após denúncia", "Remoção de Conteúdo", unit="number", synonyms=("removed after report", "report-driven removals")),
    MetricDefinition("content_removed_before_view", "Conteúdo removido antes de visualização", "Remoção de Conteúdo", unit="number", synonyms=("before view", "pre-view removal", "proactive removals")),
    MetricDefinition("content_restored_after_appeal", "Conteúdo restaurado após recurso", "Transparência", unit="number", synonyms=("restored after appeal", "appeal reversals")),
    MetricDefinition("videos_removed", "Vídeos removidos", "Remoção de Conteúdo", unit="number", synonyms=("videos removed",)),
    MetricDefinition("comments_removed", "Comentários removidos", "Remoção de Conteúdo", unit="number", synonyms=("comments removed",)),
    MetricDefinition("accounts_removed", "Contas removidas", "Remoção de Conteúdo", unit="number", synonyms=("accounts removed",)),
    MetricDefinition("fake_accounts_removed", "Contas falsas removidas", "Remoção de Conteúdo", unit="number", synonyms=("fake accounts removed", "spam accounts removed")),
    MetricDefinition("reports_total", "Número de denúncias", "Denúncias", unit="number", synonyms=("reports received", "user reports", "complaints")),
    MetricDefinition("report_type", "Tipo de denúncia", "Denúncias", synonyms=("report type", "category of report")),
    MetricDefinition("report_source_user", "Origem: usuário", "Denúncias", unit="number", synonyms=("user reports", "from users")),
    MetricDefinition("report_source_auto", "Origem: sistema automático", "Denúncias", unit="number", synonyms=("automated reports", "machine reports")),
    MetricDefinition("report_source_trusted_flagger", "Origem: Trusted Flagger", "Denúncias", unit="number", synonyms=("trusted flagger", "trusted reporters")),
    MetricDefinition("report_response_time_avg", "Tempo médio de resposta", "Denúncias", unit="number", synonyms=("average response time", "median response time", "time to action")),
    MetricDefinition("child_sexual_exploitation_content", "Conteúdo de exploração sexual infantil", "Segurança Infantil", unit="number", synonyms=("child sexual exploitation", "csam")),
    MetricDefinition("csam_removed", "CSAM removido", "Segurança Infantil", unit="number", synonyms=("csam removed", "removed csam")),
    MetricDefinition("suspected_underage_accounts", "Contas suspeitas de menores", "Segurança Infantil", unit="number", synonyms=("underage accounts", "suspected minors")),
    MetricDefinition("accounts_removed_by_age", "Contas removidas por idade", "Segurança Infantil", unit="number", synonyms=("age removals", "removed for age")),
    MetricDefinition("parental_tools", "Ferramentas parentais", "ECA Digital", is_boolean=True, synonyms=("parental tools", "family pairing")),
    MetricDefinition("message_controls", "Controle de mensagens", "ECA Digital", is_boolean=True, synonyms=("message controls", "direct message controls")),
    MetricDefinition("time_limit", "Limite de tempo", "ECA Digital", is_boolean=True, synonyms=("screen time", "time limits")),
    MetricDefinition("teen_private_default", "Configuração privada para adolescentes", "ECA Digital", is_boolean=True, synonyms=("teen private default", "private by default")),
    MetricDefinition("ai_detection_automatic", "Detecção automática", "Inteligência Artificial", unit="number", synonyms=("automated detection", "ai detection")),
    MetricDefinition("ai_precision", "Precisão", "Inteligência Artificial", unit="number", synonyms=("precision", "accuracy")),
    MetricDefinition("proactive_removal_rate", "Taxa de remoção proativa", "Inteligência Artificial", unit="number", synonyms=("proactive removal rate",)),
    MetricDefinition("ai_usage", "Uso de IA", "Inteligência Artificial", is_boolean=True, synonyms=("ai usage", "use of ai", "machine learning")),
    MetricDefinition("appeals_total", "Quantidade de recursos", "Transparência", unit="number", synonyms=("appeals", "reviews", "submissions")),
    MetricDefinition("appeals_accepted", "Recursos aceitos", "Transparência", unit="number", synonyms=("appeals accepted", "upheld appeals")),
    MetricDefinition("appeals_denied", "Recursos negados", "Transparência", unit="number", synonyms=("appeals denied", "rejected appeals")),
    MetricDefinition("lgpd_download_data", "Possui download de dados", "LGPD", is_boolean=True, synonyms=("download your data", "download data")),
    MetricDefinition("lgpd_delete_data", "Possui exclusão", "LGPD", is_boolean=True, synonyms=("delete account", "delete data")),
    MetricDefinition("lgpd_portability", "Possui portabilidade", "LGPD", is_boolean=True, synonyms=("data portability",)),
    MetricDefinition("lgpd_consent", "Possui consentimento", "LGPD", is_boolean=True, synonyms=("consent",)),
    MetricDefinition("lgpd_withdrawal", "Possui revogação", "LGPD", is_boolean=True, synonyms=("withdraw consent", "revoke consent")),
    MetricDefinition("lgpd_clear_policy", "Possui política clara", "LGPD", is_boolean=True, synonyms=("privacy policy",)),
    MetricDefinition("lgpd_privacy_dashboard", "Possui painel de privacidade", "LGPD", is_boolean=True, synonyms=("privacy dashboard",)),
    MetricDefinition("eca_parental_control", "Controle parental", "ECA Digital", is_boolean=True, synonyms=("parental control",)),
    MetricDefinition("eca_age_verification", "Verificação de idade", "ECA Digital", is_boolean=True, synonyms=("age verification",)),
    MetricDefinition("eca_teen_protection", "Proteção de adolescentes", "ECA Digital", is_boolean=True, synonyms=("teen protection",)),
    MetricDefinition("eca_private_default", "Configuração privada padrão", "ECA Digital", is_boolean=True, synonyms=("private by default", "default private")),
    MetricDefinition("eca_unknown_contact_protection", "Proteção contra contato de desconhecidos", "ECA Digital", is_boolean=True, synonyms=("unknown contact protection", "stranger protection")),
    MetricDefinition("eca_guardian_tools", "Ferramentas para responsáveis", "ECA Digital", is_boolean=True, synonyms=("guardian tools", "family center")),
]


METRIC_BY_CODE = {definition.code: definition for definition in METRIC_DEFINITIONS}


def metric_codes() -> list[str]:
    return [definition.code for definition in METRIC_DEFINITIONS]


def find_definition_by_label(label: str) -> MetricDefinition | None:
    normalized = label.lower()
    for definition in METRIC_DEFINITIONS:
        haystack = " ".join((definition.name, definition.official_label or "", definition.description or "", *definition.synonyms)).lower()
        if normalized in haystack:
            return definition
    return None


def definitions_for_category(category: str) -> list[MetricDefinition]:
    return [definition for definition in METRIC_DEFINITIONS if definition.category == category]


def all_categories() -> list[str]:
    return sorted({definition.category for definition in METRIC_DEFINITIONS})
