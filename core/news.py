"""
core/news.py — Nexara Skills Warehouse
Top news headlines via NewsAPI-compatible free endpoint.
Falls back to RSS scraping if no API key is set.

Dependencies: httpx, beautifulsoup4, lxml
Platforms   : all
"""

import os
import httpx
from bs4 import BeautifulSoup
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=20, write=5, pool=5)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")


class NewsSkill(BaseSkill):
    name        = "news"
    description = (
        "Fetch top news headlines. "
        "Args: query (str opt), category ('technology'|'science'|'business'|'health'|'sports'|'general'), "
        "country (str, default 'us'), limit (int, default 5)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        query:    str = "",
        category: str = "general",
        country:  str = "us",
        limit:    int = 5,
        **kwargs,
    ):
        limit = max(1, min(10, limit))
        if NEWSAPI_KEY:
            return await self._newsapi(query, category, country, limit)
        return await self._rss(query, limit)

    async def _newsapi(self, query, category, country, limit):
        params = {"apiKey": NEWSAPI_KEY, "pageSize": limit, "country": country}
        if query:
            params["q"] = query
            url = "https://newsapi.org/v2/everything"
        else:
            params["category"] = category
            url = "https://newsapi.org/v2/top-headlines"
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
            articles = resp.json().get("articles", [])[:limit]
            if not articles:
                return SkillResult(success=False, output="", error="No articles found.")
            lines = [f"📰 **Top News**\n"]
            for a in articles:
                lines.append(f"**{a.get('title','?')}**")
                if a.get("description"):
                    lines.append(f"_{a['description'][:120]}_")
                lines.append(f"🔗 {a.get('url','')}\n")
            return SkillResult(success=True, output="\n".join(lines), data={"count": len(articles)})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

    async def _rss(self, query, limit):
        # Free RSS fallback — BBC News
        feeds = {
            "": "https://feeds.bbci.co.uk/news/rss.xml",
            "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
            "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
            "health": "https://feeds.bbci.co.uk/news/health/rss.xml",
            "sports": "https://feeds.bbci.co.uk/sport/rss.xml",
        }
        url = feeds.get("")
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": "Nexara/1.0"}) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            soup  = BeautifulSoup(resp.text, "lxml-xml")
            items = soup.find_all("item")[:limit]
            if not items:
                return SkillResult(success=False, output="", error="No RSS items found.")
            lines = ["📰 **BBC News Headlines**\n"]
            for item in items:
                title = item.find("title")
                link  = item.find("link")
                desc  = item.find("description")
                lines.append(f"**{title.text if title else '??'}**")
                if desc and desc.text:
                    lines.append(f"_{BeautifulSoup(desc.text, 'lxml').get_text()[:120]}_")
                if link:
                    lines.append(f"🔗 {link.text}\n")
            return SkillResult(success=True, output="\n".join(lines), data={"count": len(items)})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
