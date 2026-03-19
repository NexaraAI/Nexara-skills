"""
core/url_shorten.py — Nexara Skills Warehouse
Shorten URLs via TinyURL (free, no API key needed).

Dependencies: httpx
Platforms   : all
"""

import httpx
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=15, write=5, pool=5)


class UrlShortenSkill(BaseSkill):
    name        = "url_shorten"
    description = "Shorten a long URL using TinyURL. Args: url (str), alias (str opt)."
    platforms   = ["all"]

    async def execute(self, url: str = "", alias: str = "", **kwargs):
        if not url:
            return SkillResult(success=False, output="", error="No URL provided.")
        params = {"url": url}
        if alias:
            params["alias"] = alias
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get("https://tinyurl.com/api-create.php", params=params)
                resp.raise_for_status()
            short = resp.text.strip()
            if not short.startswith("http"):
                return SkillResult(success=False, output="", error=f"Unexpected response: {short[:100]}")
            return SkillResult(
                success=True,
                output=f"🔗 **Shortened URL**\nOriginal : {url}\nShort    : {short}",
                data={"original": url, "short": short},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
