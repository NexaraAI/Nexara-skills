"""
core/rss_feed.py — Nexara Skills Warehouse
Fetch and parse RSS/Atom feeds from any URL.

Dependencies: httpx, beautifulsoup4, lxml
Platforms   : all
"""

import httpx
from bs4 import BeautifulSoup
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=20, write=5, pool=5)
HEADERS = {"User-Agent": "Nexara/1.0 RSS Reader"}


class RssFeedSkill(BaseSkill):
    name        = "rss_feed"
    description = (
        "Fetch and parse an RSS or Atom feed. "
        "Args: url (str), limit (int, default 5), summarize (bool, default True)."
    )
    platforms   = ["all"]

    async def execute(self, url: str = "", limit: int = 5, summarize: bool = True, **kwargs):
        if not url:
            return SkillResult(success=False, output="", error="No RSS URL provided.")
        limit = max(1, min(20, limit))
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
            soup  = BeautifulSoup(resp.text, "lxml-xml")
            # Try RSS <item> then Atom <entry>
            items = soup.find_all("item") or soup.find_all("entry")
            if not items:
                return SkillResult(success=False, output="", error="No feed items found. Check the URL.")

            feed_title = ""
            if soup.find("title"):
                feed_title = soup.find("title").get_text(strip=True)

            lines = [f"📡 **{feed_title or url}**\n"]
            for item in items[:limit]:
                title   = item.find("title")
                link    = item.find("link")
                summary = item.find("description") or item.find("summary") or item.find("content")
                pub     = item.find("pubDate") or item.find("published") or item.find("updated")

                t = title.get_text(strip=True) if title else "Untitled"
                l = link.get_text(strip=True) if link else (link.get("href","") if link else "")
                s = BeautifulSoup(summary.get_text(), "lxml").get_text()[:150] if summary else ""
                p = pub.get_text(strip=True)[:20] if pub else ""

                lines.append(f"**{t}**")
                if p: lines.append(f"  _{p}_")
                if summarize and s: lines.append(f"  {s}…")
                if l: lines.append(f"  🔗 {l}\n")

            return SkillResult(
                success=True,
                output="\n".join(lines),
                data={"feed": feed_title, "count": len(items[:limit])},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
