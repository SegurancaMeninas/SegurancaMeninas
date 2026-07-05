from __future__ import annotations

from app.crawlers.base import OfficialCrawler


class MetaCrawler(OfficialCrawler):
    platform_name = "Meta"
    platform_slug = "meta"
    source_url = "https://transparency.meta.com/reports/"

    def discover_links(self) -> list[dict[str, str]]:
        links = super().discover_links()
        return [link for link in links if "transparency.meta.com" in link["url"]]
