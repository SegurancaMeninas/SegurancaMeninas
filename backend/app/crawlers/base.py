from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.metric_catalog import METRIC_DEFINITIONS, MetricDefinition, find_definition_by_label


@dataclass
class CrawledArtifact:
    url: str
    source_type: str
    title: str | None
    report_date: str | None
    raw_metadata: dict[str, Any]
    content: Any
    checksum: str | None = None


class OfficialCrawler:
    platform_name: str
    platform_slug: str
    source_url: str

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    def fetch_html(self, url: str) -> BeautifulSoup:
        response = self.session.get(url, timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def fetch_bytes(self, url: str) -> bytes:
        response = self.session.get(url, timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        return response.content

    def discover_links(self) -> list[dict[str, str]]:
        soup = self.fetch_html(self.source_url)
        links: list[dict[str, str]] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            text = " ".join(anchor.get_text(" ", strip=True).split())
            if not href.startswith("http"):
                href = requests.compat.urljoin(self.source_url, href)
            if any(token in href.lower() for token in ("csv", "json", "xlsx", "xls", "report", "transparency")) or any(
                token in text.lower() for token in ("report", "transparency", "download", "csv", "json")
            ):
                links.append({"url": href, "title": text})
        return self._dedupe(links)

    def _dedupe(self, items: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        result: list[dict[str, str]] = []
        for item in items:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            result.append(item)
        return result

    def _checksum(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return settings.cache_dir / f"{self.platform_slug}_{digest}"

    def download_artifact(self, url: str, title: str | None = None) -> CrawledArtifact:
        lowered = url.lower()
        raw_metadata = {"title": title, "platform": self.platform_name, "platform_slug": self.platform_slug}
        if lowered.endswith(".csv"):
            payload = self.fetch_bytes(url)
            content = pd.read_csv(io.BytesIO(payload))
            return CrawledArtifact(url=url, source_type="csv", title=title, report_date=None, raw_metadata=raw_metadata, content=content, checksum=self._checksum(payload))
        if lowered.endswith((".json", ".json?hl=en")):
            payload = self.fetch_bytes(url)
            content = json.loads(payload.decode("utf-8"))
            return CrawledArtifact(url=url, source_type="json", title=title, report_date=None, raw_metadata=raw_metadata, content=content, checksum=self._checksum(payload))
        if lowered.endswith((".xlsx", ".xls")):
            payload = self.fetch_bytes(url)
            content = pd.read_excel(io.BytesIO(payload))
            return CrawledArtifact(url=url, source_type="excel", title=title, report_date=None, raw_metadata=raw_metadata, content=content, checksum=self._checksum(payload))
        soup = self.fetch_html(url)
        raw_metadata["page_title"] = soup.title.get_text(strip=True) if soup.title else title
        raw_tables = pd.read_html(str(soup)) if soup.find("table") else []
        return CrawledArtifact(url=url, source_type="html", title=title or raw_metadata.get("page_title"), report_date=None, raw_metadata=raw_metadata, content={"html": str(soup), "tables": raw_tables}, checksum=None)

    def extract_metric_rows(self, artifact: CrawledArtifact) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if artifact.source_type in {"csv", "excel"}:
            dataframe = artifact.content
            rows.extend(self._rows_from_dataframe(dataframe))
        elif artifact.source_type == "json":
            rows.extend(self._rows_from_json(artifact.content))
        elif artifact.source_type == "html":
            for table in artifact.content.get("tables", []):
                rows.extend(self._rows_from_dataframe(table))
        return rows

    def _rows_from_dataframe(self, dataframe: pd.DataFrame) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        normalized_columns = [str(column).strip().lower() for column in dataframe.columns]
        if len(dataframe.index) == 1:
            row = dataframe.iloc[0].to_dict()
            rows.extend(self._match_row(row))
            return rows
        for _, series in dataframe.iterrows():
            rows.extend(self._match_row(series.to_dict()))
        if not rows:
            for column_name in normalized_columns:
                definition = find_definition_by_label(column_name)
                if definition:
                    rows.append({"metric_code": definition.code, "metric_name": definition.name, "value": None})
        return rows

    def _rows_from_json(self, content: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    rows.extend(self._match_row(item))
        elif isinstance(content, dict):
            rows.extend(self._match_row(content))
        return rows

    def _match_row(self, row: dict[str, Any]) -> list[dict[str, Any]]:
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        matches: list[dict[str, Any]] = []
        for key, value in normalized.items():
            definition = find_definition_by_label(key)
            if definition is None:
                continue
            matches.append(self._coerce_metric_value(definition, value, row))
        return matches

    def _coerce_metric_value(self, definition: MetricDefinition, value: Any, row: dict[str, Any]) -> dict[str, Any]:
        if definition.is_boolean:
            normalized = str(value).strip().lower()
            boolean_value = normalized in {"1", "true", "yes", "sim", "y"}
            return {"metric_code": definition.code, "metric_name": definition.name, "value": boolean_value, "raw": row}
        try:
            numeric_value = float(str(value).replace("%", "").replace(",", ""))
            return {"metric_code": definition.code, "metric_name": definition.name, "value": numeric_value, "raw": row}
        except (TypeError, ValueError):
            text_value = str(value).strip()
            return {"metric_code": definition.code, "metric_name": definition.name, "value": text_value or None, "raw": row}

    def find_quarter_and_year(self, text: str | None) -> tuple[int | None, int | None, str | None]:
        if not text:
            return None, None, None
        text = " ".join(text.split())
        quarter_match = re.search(r"(Q[1-4]|1st quarter|2nd quarter|3rd quarter|4th quarter|H1|H2)", text, re.IGNORECASE)
        year_match = re.search(r"(20\d{2})", text)
        quarter = None
        if quarter_match:
            token = quarter_match.group(1).upper()
            if token.startswith("Q"):
                quarter = int(token[1])
            elif token == "H1":
                quarter = 1
            elif token == "H2":
                quarter = 3
            else:
                quarter = 1 if "1" in token or "2" in token else 3
        year = int(year_match.group(1)) if year_match else None
        label = f"{year} {quarter if quarter else ''}".strip() if year else text
        return quarter, year, label
