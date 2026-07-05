from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawlers.registry import CRAWLERS
from app.models.entities import Metric, MetricValue, Platform, Quarter, Report, Source
from app.services.indicator_service import calculate_and_persist_scores, upsert_default_indicators
from app.services.metric_catalog import METRIC_DEFINITIONS


PLATFORMS = [
    {
        "name": "Meta",
        "slug": "meta",
        "official_url": "https://transparency.meta.com/",
        "description": "Meta Transparency Center and reports.",
    },
    {
        "name": "TikTok",
        "slug": "tiktok",
        "official_url": "https://www.tiktok.com/transparency/",
        "description": "TikTok Transparency Center and report pages.",
    },
    {
        "name": "YouTube",
        "slug": "youtube",
        "official_url": "https://transparencyreport.google.com/",
        "description": "Google Transparency Report pages relevant to YouTube.",
    },
]


def seed_reference_data(db: Session) -> None:
    existing_platforms = {platform.slug: platform for platform in db.scalars(select(Platform)).all()}
    for payload in PLATFORMS:
        if payload["slug"] not in existing_platforms:
            db.add(Platform(**payload))
    existing_metrics = {metric.code for metric in db.scalars(select(Metric)).all()}
    for definition in METRIC_DEFINITIONS:
        if definition.code not in existing_metrics:
            db.add(
                Metric(
                    code=definition.code,
                    name=definition.name,
                    category=definition.category,
                    description=definition.description,
                    unit=definition.unit,
                    official_label=definition.official_label,
                    is_boolean=definition.is_boolean,
                )
            )
    db.commit()
    upsert_default_indicators(db)


def ensure_quarter(db: Session, year: int | None, quarter: int | None, label: str | None) -> Quarter | None:
    if year is None or quarter is None:
        return None
    existing = db.scalar(select(Quarter).where(Quarter.year == year, Quarter.quarter == quarter))
    if existing:
        return existing
    quarter_label = label or f"{year} Q{quarter}"
    quarter_row = Quarter(year=year, quarter=quarter, label=quarter_label)
    db.add(quarter_row)
    db.commit()
    db.refresh(quarter_row)
    return quarter_row


def store_artifact(db: Session, crawler, artifact, report_title: str | None = None) -> dict[str, Any]:
    platform = db.scalar(select(Platform).where(Platform.slug == crawler.platform_slug))
    if platform is None:
        raise ValueError(f"Platform not seeded: {crawler.platform_slug}")

    quarter, year, period_label = crawler.find_quarter_and_year(artifact.title or report_title or artifact.url)
    quarter_row = ensure_quarter(db, year, quarter, period_label)

    source = Source(
        platform_id=platform.id,
        url=artifact.url,
        source_type=artifact.source_type,
        title=artifact.title,
        report_date=artifact.report_date,
        checksum=artifact.checksum,
        raw_metadata_json=json.dumps(artifact.raw_metadata, ensure_ascii=False),
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    report = Report(
        platform_id=platform.id,
        quarter_id=quarter_row.id if quarter_row else None,
        source_id=source.id,
        title=artifact.title or report_title or platform.name,
        report_type=artifact.source_type,
        published_at=datetime.now(timezone.utc),
        reference_url=artifact.url,
        report_period_label=period_label,
        raw_metadata_json=json.dumps(artifact.raw_metadata, ensure_ascii=False),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    extracted_rows = crawler.extract_metric_rows(artifact)
    stored_values: list[MetricValue] = []
    metric_index = {metric.code: metric for metric in db.scalars(select(Metric)).all()}
    for row in extracted_rows:
        metric_code = row.get("metric_code")
        if metric_code not in metric_index:
            continue
        metric = metric_index[metric_code]
        value = row.get("value")
        stored = MetricValue(
            report_id=report.id,
            metric_id=metric.id,
            source_id=source.id,
            value_text=str(value) if value is not None else None,
            value_number=float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None,
            disclosure_status="officially_disclosed" if value is not None else "not_disclosed",
            source_url=artifact.url,
            report_period_label=period_label,
            raw_data_json=json.dumps(row, ensure_ascii=False),
        )
        stored_values.append(stored)
        db.add(stored)
    db.commit()

    scores = calculate_and_persist_scores(db, platform, quarter_row, stored_values)
    for score in scores:
        db.add(score)
    db.commit()

    return {"platform": platform.name, "source_url": artifact.url, "report_id": report.id, "values": len(stored_values)}


def refresh_all_sources(db: Session) -> dict[str, Any]:
    seed_reference_data(db)
    summary = {"processed": 0, "reports": 0, "metric_values": 0, "sources": []}
    for crawler in CRAWLERS:
        links = crawler.discover_links()
        for link in links[:20]:
            try:
                artifact = crawler.download_artifact(link["url"], link.get("title"))
                result = store_artifact(db, crawler, artifact, link.get("title"))
                summary["processed"] += 1
                summary["reports"] += 1
                summary["metric_values"] += result["values"]
                summary["sources"].append(result)
            except Exception as exc:
                summary.setdefault("errors", []).append({"platform": crawler.platform_name, "url": link["url"], "error": str(exc)})
    return summary
