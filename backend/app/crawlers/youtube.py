from __future__ import annotations

from app.crawlers.base import OfficialCrawler


class YouTubeCrawler(OfficialCrawler):
    platform_name = "YouTube"
    platform_slug = "youtube"
    source_url = "https://transparencyreport.google.com/youtube-policy"

    def discover_links(self) -> list[dict[str, str]]:
        base_links = super().discover_links()
        extras = [
            {"url": "https://transparencyreport.google.com/child-sexual-abuse-material", "title": "CSAM Transparency Report"},
            {"url": "https://transparencyreport.google.com/child-sexual-abuse-material/reporting?hl=en", "title": "CSAM Reporting"},
            {"url": "https://transparencyreport.google.com/youtube-policy", "title": "YouTube Community Guidelines enforcement"},
            {"url": "https://transparencyreport.google.com/youtube-copyright", "title": "YouTube Copyright Transparency Report"},
        ]
        return self._dedupe(base_links + extras)
