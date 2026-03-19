"""
core/web_search.py — Nexara Skills Warehouse
DuckDuckGo web search — returns titles, URLs, and snippets.

Dependencies: httpx, beautifulsoup4, lxml
Platforms   : all
"""

import logging
from urllib.parse import unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from skills.base import BaseSkill, SkillResult

logger = logging.getLogger("nexara.skill.web_search")

DDG_URL = "https://html.duckduckgo.com/html/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)


class WebSearchSkill(BaseSkill):
    name        = "web_search"
    description = "Search the web using DuckDuckGo. Returns titles, URLs, and snippets."
    platforms   = ["all"]

    async def execute(self, query: str = "", **kwargs) -> SkillResult:
        if not query:
            return SkillResult(success=False, output="", error="No query provided.")

        try:
            async with httpx.AsyncClient(
                headers=HEADERS, follow_redirects=True, timeout=TIMEOUT
            ) as client:
                resp = await client.post(DDG_URL, data={"q": query})
                resp.raise_for_status()

            soup   = BeautifulSoup(resp.text, "lxml")
            blocks = (
                soup.select("div.result")
                or soup.select("div.web-result")
                or []
            )
            results = []

            for block in blocks[:8]:
                title_tag   = (
                    block.select_one("a.result__a")
                    or block.select_one("h2 a")
                    or block.select_one("a[href]")
                )
                snippet_tag = block.select_one("a.result__snippet") or block.select_one(".result__snippet")

                if not title_tag:
                    continue

                title   = title_tag.get_text(strip=True)
                url     = title_tag.get("href", "")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                if "uddg=" in url:
                    from urllib.parse import parse_qs
                    qs  = parse_qs(urlparse(url).query)
                    url = unquote(qs.get("uddg", [url])[0])

                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet})

            if not results:
                return SkillResult(success=False, output="", error="No results found.")

            lines = [f"🔍 **Results for** `{query}`\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"**{i}. {r['title']}**")
                if r["snippet"]:
                    lines.append(f"   _{r['snippet']}_")
                lines.append(f"   {r['url']}\n")

            return SkillResult(
                success=True,
                output="\n".join(lines),
                data={"results": results, "count": len(results)},
            )

        except httpx.HTTPStatusError as exc:
            return SkillResult(success=False, output="", error=f"HTTP {exc.response.status_code}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
