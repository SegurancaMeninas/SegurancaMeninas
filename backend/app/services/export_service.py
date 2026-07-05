from __future__ import annotations

import csv
import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import MetricValue, Platform, Report
from app.services.disclosure_service import disclosure_text
from app.services.indicator_service import calculate_indicator_results


def export_excel(db: Session) -> bytes:
    reports = db.scalars(select(Report)).all()
    values = db.scalars(select(MetricValue)).all()
    report_rows = [
        {
            "platform_id": report.platform_id,
            "quarter_id": report.quarter_id,
            "source_id": report.source_id,
            "title": report.title,
            "report_type": report.report_type,
            "published_at": report.published_at.isoformat() if report.published_at else None,
            "reference_url": report.reference_url,
            "report_period_label": report.report_period_label,
        }
        for report in reports
    ]
    metric_rows = [
        {
            "report_id": value.report_id,
            "metric_id": value.metric_id,
            "value_text": value.value_text,
            "value_number": value.value_number,
            "disclosure_status": value.disclosure_status,
            "source_url": value.source_url,
            "report_period_label": value.report_period_label,
        }
        for value in values
    ]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(report_rows).to_excel(writer, sheet_name="Reports", index=False)
        pd.DataFrame(metric_rows).to_excel(writer, sheet_name="MetricValues", index=False)
    return output.getvalue()


def export_csv(db: Session) -> bytes:
    values = db.scalars(select(MetricValue)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["report_id", "metric_id", "value_text", "value_number", "disclosure_status", "source_url", "report_period_label"])
    for value in values:
        writer.writerow([value.report_id, value.metric_id, value.value_text, value.value_number, value.disclosure_status, value.source_url, value.report_period_label])
    return output.getvalue().encode("utf-8")


def _build_summary_dataframe(db: Session) -> pd.DataFrame:
    values = db.scalars(select(MetricValue)).all()
    rows = []
    for value in values:
        rows.append(
            {
                "platform": value.report.platform.name if value.report and value.report.platform else None,
                "metric": value.metric.name if value.metric else None,
                "value": disclosure_text(value.value_number if value.value_number is not None else value.value_text),
                "source_url": value.source_url,
                "report_period_label": value.report_period_label,
            }
        )
    return pd.DataFrame(rows)


def export_pdf(db: Session) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, title="Social Platform Transparency Dashboard")
    styles = getSampleStyleSheet()
    elements = [Paragraph("Social Platform Transparency Dashboard", styles["Title"]), Spacer(1, 12)]
    summary_df = _build_summary_dataframe(db)
    indicators = calculate_indicator_results(db.query(MetricValue).all())
    elements.append(Paragraph("Resumo executivo", styles["Heading2"]))
    elements.append(Paragraph(f"Total de métricas armazenadas: {len(summary_df)}", styles["BodyText"]))
    elements.append(Spacer(1, 8))

    if not summary_df.empty:
        table_data = [summary_df.columns.tolist()] + summary_df.head(20).fillna("-").values.tolist()
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#94a3b8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Indicadores calculados", styles["Heading2"]))
    indicator_data = [["Indicador", "Pontuação"]] + [[item.name, f"{item.score:.2f}" if item.score is not None else "Não divulgado oficialmente"] for item in indicators]
    indicator_table = Table(indicator_data, repeatRows=1)
    indicator_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#94a3b8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(indicator_table)
    elements.append(Spacer(1, 12))

    document.build(elements)
    return buffer.getvalue()
