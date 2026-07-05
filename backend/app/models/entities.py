from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Platform(Base, TimestampMixin):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    official_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reports: Mapped[list[Report]] = relationship("Report", back_populates="platform")


class Quarter(Base, TimestampMixin):
    __tablename__ = "quarters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    report_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    raw_metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    platform: Mapped[Platform] = relationship("Platform")
    reports: Mapped[list[Report]] = relationship("Report", back_populates="source")


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    quarter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quarters.id"), nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reference_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    report_period_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    raw_metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    platform: Mapped[Platform] = relationship("Platform", back_populates="reports")
    source: Mapped[Source] = relationship("Source", back_populates="reports")
    quarter: Mapped[Optional[Quarter]] = relationship("Quarter")
    values: Mapped[list[MetricValue]] = relationship("MetricValue", back_populates="report")


class Metric(Base, TimestampMixin):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="text")
    official_label: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_boolean: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_indicator_input: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    values: Mapped[list[MetricValue]] = relationship("MetricValue", back_populates="metric")


class MetricValue(Base, TimestampMixin):
    __tablename__ = "metric_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_number: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    disclosure_status: Mapped[str] = mapped_column(String(80), nullable=False, default="officially_disclosed")
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    report_period_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    raw_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    report: Mapped[Report] = relationship("Report", back_populates="values")
    metric: Mapped[Metric] = relationship("Metric", back_populates="values")
    source: Mapped[Source] = relationship("Source")


class Indicator(Base, TimestampMixin):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ComplianceScore(Base, TimestampMixin):
    __tablename__ = "compliance_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    quarter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quarters.id"), nullable=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    platform: Mapped[Platform] = relationship("Platform")
    quarter: Mapped[Optional[Quarter]] = relationship("Quarter")
    indicator: Mapped[Indicator] = relationship("Indicator")
