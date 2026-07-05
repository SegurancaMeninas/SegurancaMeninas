from __future__ import annotations

from app.crawlers.meta import MetaCrawler
from app.crawlers.tiktok import TikTokCrawler
from app.crawlers.youtube import YouTubeCrawler

CRAWLERS = [MetaCrawler(), TikTokCrawler(), YouTubeCrawler()]
