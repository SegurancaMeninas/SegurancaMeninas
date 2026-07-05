from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlatformSummary(BaseModel):
    platform: str
    last_update: datetime | None = None
    metric_count: int = 0
    report_count: int = 0
    score_transparency: float | None = None
    score_lgpd: float | None = None
    score_eca: float | None = None


class DashboardSummary(BaseModel):
    last_update: datetime | None = None
    metric_count: int = 0
    report_count: int = 0
    platform_cards: list[PlatformSummary] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    platform: str
    quarter: str | None = None
    year: int | None = None
    metric: str
    value: str
    source_url: str
    report_date: datetime | None = None
    report_period_label: str | None = None


class IndicatorReading(BaseModel):
    code: str
    name: str
    score: float | None = None
    notes: str | None = None


class ReportSummary(BaseModel):
    id: int
    platform: str
    title: str
    report_type: str
    reference_url: str
    report_period_label: str | None = None
    published_at: datetime | None = None


class MetricReading(BaseModel):
    platform: str
    metric_code: str
    metric_name: str
    category: str
    value: str
    source_url: str
    report_period_label: str | None = None
    disclosure_status: str


class RefreshResponse(BaseModel):
    processed: int
    reports: int
    metric_values: int
    sources: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
