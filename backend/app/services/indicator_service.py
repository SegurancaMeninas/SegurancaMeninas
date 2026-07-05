from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ComplianceScore, Indicator, Metric, MetricValue, Platform, Quarter
from app.services.metric_catalog import METRIC_BY_CODE


@dataclass
class IndicatorResult:
    code: str
    name: str
    score: float
    notes: str | None = None


def _latest_metric_value(values: list[MetricValue], metric_code: str) -> MetricValue | None:
    candidates = [value for value in values if value.metric and value.metric.code == metric_code]
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.collected_at, reverse=True)
    return candidates[0]


def _number_from_metric(values: list[MetricValue], metric_code: str) -> float | None:
    latest = _latest_metric_value(values, metric_code)
    if latest is None:
        return None
    if latest.value_number is not None:
        return float(latest.value_number)
    try:
        return float(str(latest.value_text).replace("%", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(float(numerator) / float(denominator), 4)


def calculate_indicator_results(values: list[MetricValue]) -> list[IndicatorResult]:
    removed_total = _number_from_metric(values, "content_removed_total")
    removed_auto = _number_from_metric(values, "content_removed_automatic")
    appeals = _number_from_metric(values, "appeals_total")
    appeals_accepted = _number_from_metric(values, "appeals_accepted")
    removed_before_view = _number_from_metric(values, "content_removed_before_view")
    reports_total = _number_from_metric(values, "reports_total")

    transparency_ratio = safe_ratio(len([value for value in values if value.disclosure_status == "officially_disclosed"]), max(len(values), 1))
    lgpd_score = round(
        100 * sum(
            1
            for code in ["lgpd_download_data", "lgpd_delete_data", "lgpd_portability", "lgpd_consent", "lgpd_withdrawal", "lgpd_clear_policy", "lgpd_privacy_dashboard"]
            if _latest_metric_value(values, code) and str(_latest_metric_value(values, code).value_text).strip().lower() == "true"
        )
        / 7,
        2,
    ) if values else 0.0
    eca_score = round(
        100 * sum(
            1
            for code in ["eca_parental_control", "eca_age_verification", "eca_teen_protection", "eca_private_default", "eca_unknown_contact_protection", "eca_guardian_tools"]
            if _latest_metric_value(values, code) and str(_latest_metric_value(values, code).value_text).strip().lower() == "true"
        )
        / 6,
        2,
    ) if values else 0.0

    indicators = [
        IndicatorResult("taxa_remocao", "Taxa de remoção", safe_ratio(removed_total, reports_total), "conteúdo removido / conteúdo denunciado"),
        IndicatorResult("taxa_detecao_automatica", "Taxa de detecção automática", safe_ratio(removed_auto, removed_total), "remoções automáticas / remoções totais"),
        IndicatorResult("taxa_recursos_aceitos", "Taxa de recursos aceitos", safe_ratio(appeals_accepted, appeals), "recursos aceitos / recursos"),
        IndicatorResult("taxa_remocao_preventiva", "Taxa de remoção preventiva", safe_ratio(removed_before_view, removed_total), "conteúdo removido antes da visualização / conteúdo removido"),
        IndicatorResult("indice_transparencia", "Índice de Transparência", transparency_ratio * 100 if transparency_ratio is not None else 0.0, "baseado na disponibilidade oficial dos dados"),
        IndicatorResult("indice_lgpd", "Índice LGPD", lgpd_score, "baseado em checklist oficial disponível"),
        IndicatorResult("indice_eca", "Índice ECA Digital", eca_score, "baseado em checklist oficial disponível"),
    ]
    return indicators


def upsert_default_indicators(db: Session) -> None:
    indicator_rows = [
        ("taxa_remocao", "Taxa de remoção", "Indicador", "conteúdo removido / conteúdo denunciado"),
        ("taxa_detecao_automatica", "Taxa de detecção automática", "Indicador", "remoções automáticas / remoções totais"),
        ("taxa_recursos_aceitos", "Taxa de recursos aceitos", "Indicador", "recursos aceitos / recursos"),
        ("taxa_remocao_preventiva", "Taxa de remoção preventiva", "Indicador", "conteúdo removido antes da visualização / conteúdo removido"),
        ("indice_transparencia", "Índice de Transparência", "Indicador", "quantidade, granularidade e frequência de métricas oficiais"),
        ("indice_lgpd", "Índice LGPD", "Indicador", "checklist de recursos de privacidade"),
        ("indice_eca", "Índice ECA Digital", "Indicador", "checklist de proteção infantil e adolescente"),
    ]
    existing = {indicator.code for indicator in db.scalars(select(Indicator)).all()}
    for code, name, category, formula in indicator_rows:
        if code not in existing:
            db.add(Indicator(code=code, name=name, category=category, formula=formula))
    db.commit()


def calculate_and_persist_scores(db: Session, platform: Platform, quarter: Quarter | None, values: list[MetricValue]) -> list[ComplianceScore]:
    upsert_default_indicators(db)
    indicators = {indicator.code: indicator for indicator in db.scalars(select(Indicator)).all()}
    results = calculate_indicator_results(values)
    scores: list[ComplianceScore] = []
    for result in results:
        indicator = indicators[result.code]
        score = ComplianceScore(
            platform_id=platform.id,
            quarter_id=quarter.id if quarter else None,
            indicator_id=indicator.id,
            score=float(result.score or 0.0),
            notes=result.notes,
            report_count=len({value.report_id for value in values}),
        )
        scores.append(score)
    return scores
