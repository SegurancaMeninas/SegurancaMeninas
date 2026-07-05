from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, get_db
from app.models.entities import ComplianceScore, Indicator, Metric, MetricValue, Platform, Report, Source
from app.schemas.api import ComparisonRow, DashboardSummary, IndicatorReading, MetricReading, PlatformSummary, RefreshResponse, ReportSummary
from app.services.disclosure_service import disclosure_text
from app.services.export_service import export_csv, export_excel, export_pdf
from app.services.ingestion_service import refresh_all_sources, seed_reference_data
from app.services.indicator_service import calculate_indicator_results, upsert_default_indicators

Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        seed_reference_data(db)
    finally:
        db.close()

    if not scheduler.running:
        scheduler.add_job(
            lambda: _run_refresh_job(),
            trigger="interval",
            minutes=settings.scheduler_interval_minutes,
            id="refresh_transparency_reports",
            replace_existing=True,
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _run_refresh_job() -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        refresh_all_sources(db)
    finally:
        db.close()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    platform_rows = []
    for platform in db.scalars(select(Platform)).all():
        reports = db.query(Report).filter(Report.platform_id == platform.id).all()
        metric_values = db.query(MetricValue).join(Report).filter(Report.platform_id == platform.id).all()
        indicators = calculate_indicator_results(metric_values)
        score_map = {indicator.code: indicator.score for indicator in indicators}
        last_report = max((report.published_at for report in reports if report.published_at), default=None)
        platform_rows.append(
            PlatformSummary(
                platform=platform.name,
                last_update=last_report,
                metric_count=len(metric_values),
                report_count=len(reports),
                score_transparency=score_map.get("indice_transparencia"),
                score_lgpd=score_map.get("indice_lgpd"),
                score_eca=score_map.get("indice_eca"),
            )
        )

    all_reports = db.query(Report).all()
    all_metric_values = db.query(MetricValue).all()
    last_update = max((report.published_at for report in all_reports if report.published_at), default=None)
    return DashboardSummary(
        last_update=last_update,
        metric_count=len(all_metric_values),
        report_count=len(all_reports),
        platform_cards=platform_rows,
    )


@app.get("/metrics", response_model=list[MetricReading])
def metrics(platform: str | None = None, db: Session = Depends(get_db)) -> list[MetricReading]:
    query = db.query(MetricValue).join(Metric).join(Report).join(Platform)
    if platform:
        query = query.filter(Platform.slug == platform)
    rows = []
    for value in query.order_by(MetricValue.collected_at.desc()).all():
        rows.append(
            MetricReading(
                platform=value.report.platform.name,
                metric_code=value.metric.code,
                metric_name=value.metric.name,
                category=value.metric.category,
                value=disclosure_text(value.value_number if value.value_number is not None else value.value_text),
                source_url=value.source_url,
                report_period_label=value.report_period_label,
                disclosure_status=value.disclosure_status,
            )
        )
    return rows


@app.get("/reports", response_model=list[ReportSummary])
def reports(db: Session = Depends(get_db)) -> list[ReportSummary]:
    rows = []
    for report in db.query(Report).order_by(Report.published_at.desc().nullslast()).all():
        rows.append(
            ReportSummary(
                id=report.id,
                platform=report.platform.name,
                title=report.title,
                report_type=report.report_type,
                reference_url=report.reference_url,
                report_period_label=report.report_period_label,
                published_at=report.published_at,
            )
        )
    return rows


@app.get("/indicators", response_model=list[IndicatorReading])
def indicators(db: Session = Depends(get_db)) -> list[IndicatorReading]:
    values = db.query(MetricValue).all()
    results = calculate_indicator_results(values)
    return [IndicatorReading(code=item.code, name=item.name, score=item.score, notes=item.notes) for item in results]


@app.get("/comparison", response_model=list[ComparisonRow])
def comparison(platform: str | None = None, year: int | None = None, quarter: int | None = None, db: Session = Depends(get_db)) -> list[ComparisonRow]:
    query = db.query(MetricValue).join(Metric).join(Report).join(Platform)
    if platform:
        query = query.filter(Platform.slug == platform)
    if year and quarter:
        query = query.filter(Report.report_period_label.contains(str(year)))
    rows = []
    for value in query.order_by(MetricValue.collected_at.desc()).all():
        rows.append(
            ComparisonRow(
                platform=value.report.platform.name,
                quarter=value.report.report_period_label,
                year=value.report.published_at.year if value.report.published_at else None,
                metric=value.metric.name,
                value=disclosure_text(value.value_number if value.value_number is not None else value.value_text),
                source_url=value.source_url,
                report_date=value.report.published_at,
                report_period_label=value.report.report_period_label,
            )
        )
    return rows


@app.post("/refresh", response_model=RefreshResponse)
def refresh(db: Session = Depends(get_db)) -> RefreshResponse:
    result = refresh_all_sources(db)
    return RefreshResponse(**result)


@app.get("/export/excel")
def download_excel(db: Session = Depends(get_db)) -> Response:
    content = export_excel(db)
    return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=social-platform-transparency.xlsx"})


@app.get("/export/csv")
def download_csv(db: Session = Depends(get_db)) -> Response:
    content = export_csv(db)
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=social-platform-transparency.csv"})


@app.get("/export/pdf")
def download_pdf(db: Session = Depends(get_db)) -> Response:
    content = export_pdf(db)
    return Response(content=content, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=social-platform-transparency.pdf"})


@app.get("/platforms")
def platforms(db: Session = Depends(get_db)) -> list[dict[str, str | int]]:
    return [
        {"id": platform.id, "name": platform.name, "slug": platform.slug, "official_url": platform.official_url, "description": platform.description or ""}
        for platform in db.scalars(select(Platform)).all()
    ]
