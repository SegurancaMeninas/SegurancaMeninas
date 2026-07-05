from __future__ import annotations

from app.crawlers.base import OfficialCrawler


class TikTokCrawler(OfficialCrawler):
    platform_name = "TikTok"
    platform_slug = "tiktok"
    source_url = "https://www.tiktok.com/safety/en/transparency/reports"

    def discover_links(self) -> list[dict[str, str]]:
        links = super().discover_links()
        return [link for link in links if "tiktok.com" in link["url"] and ("transparency" in link["url"] or "report" in link["url"])]
