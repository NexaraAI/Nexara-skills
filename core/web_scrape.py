"""
core/web_scrape.py — Nexara Skills Warehouse
Fetch and parse any web page — text, links, or tables.

Dependencies: httpx, beautifulsoup4, lxml
Platforms   : all
"""

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from skills.base import BaseSkill, SkillResult

logger = logging.getLogger("nexara.skill.web_scrape")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
}
TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)
NOISE_TAGS = ["script", "style", "nav", "footer", "header",
              "aside", "form", "noscript", "iframe", "svg"]


class WebScrapeSkill(BaseSkill):
    name        = "web_scrape"
    description = (
        "Fetch and parse the full content of a web page. "
        "Args: url (str), extract ('full_text'|'summary'|'links'|'tables')."
    )
    platforms   = ["all"]

    async def execute(
        self,
        url: str = "",
        extract: str = "full_text",
        **kwargs,
    ) -> SkillResult:
        if not url:
            return SkillResult(success=False, output="", error="No URL provided.")

        try:
            async with httpx.AsyncClient(
                headers=HEADERS, follow_redirects=True, timeout=TIMEOUT
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

            soup  = BeautifulSoup(resp.text, "lxml")
            for tag in soup(NOISE_TAGS):
                tag.decompose()

            title = soup.title.string.strip() if soup.title else urlparse(url).netloc

            if extract == "links":
                links = []
                for a in soup.select("a[href]")[:50]:
                    href = urljoin(url, a["href"])
                    text = a.get_text(strip=True)
                    if text and href.startswith("http"):
                        links.append(f"• [{text[:60]}]({href})")
                return SkillResult(
                    success=True,
                    output=f"🔗 **Links from** `{title}`\n\n" + "\n".join(links[:30]),
                    data={"count": len(links)},
                )

            if extract == "tables":
                tables = soup.find_all("table")
                if not tables:
                    return SkillResult(success=True, output="No tables found on page.", data={})
                parts = []
                for i, tbl in enumerate(tables[:3], 1):
                    rows      = tbl.find_all("tr")
                    text_rows = []
                    for row in rows[:12]:
                        cells = [td.get_text(strip=True)[:30] for td in row.find_all(["td", "th"])]
                        text_rows.append(" | ".join(cells))
                    parts.append(f"**Table {i}:**\n```\n" + "\n".join(text_rows) + "\n```")
                return SkillResult(success=True, output="\n\n".join(parts), data={})

            # full_text or summary
            main  = soup.find("main") or soup.find("article") or soup.find("body") or soup
            text  = re.sub(r"\n{3,}", "\n\n", main.get_text(separator="\n", strip=True))
            chars = 3000 if extract == "summary" else 6000
            trunc = len(text) > chars

            return SkillResult(
                success=True,
                output=(
                    f"🌐 **{title}**\n_{url}_\n\n"
                    + text[:chars]
                    + ("\n\n_[truncated]_" if trunc else "")
                ),
                data={"title": title, "url": url, "truncated": trunc},
            )

        except httpx.HTTPStatusError as exc:
            return SkillResult(success=False, output="", error=f"HTTP {exc.response.status_code}: {url}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
