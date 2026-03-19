"""
core/translate.py — Nexara Skills Warehouse
Text translation via MyMemory API (free, no key needed, 5000 chars/day).

Dependencies: httpx
Platforms   : all
"""

import httpx
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=20, write=5, pool=5)

LANG_MAP = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de",
    "italian": "it", "portuguese": "pt", "russian": "ru", "chinese": "zh",
    "japanese": "ja", "korean": "ko", "arabic": "ar", "hindi": "hi",
    "dutch": "nl", "polish": "pl", "turkish": "tr", "swedish": "sv",
}


class TranslateSkill(BaseSkill):
    name        = "translate"
    description = (
        "Translate text between languages. "
        "Args: text (str), to_lang (str, e.g. 'spanish' or 'es'), from_lang (str, default 'auto')."
    )
    platforms   = ["all"]

    async def execute(self, text: str = "", to_lang: str = "english", from_lang: str = "auto", **kwargs):
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        to   = LANG_MAP.get(to_lang.lower(),   to_lang.lower())
        frm  = LANG_MAP.get(from_lang.lower(), from_lang.lower())
        pair = f"{frm}|{to}" if frm != "auto" else f"autodetect|{to}"
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": text[:500], "langpair": pair},
                )
                resp.raise_for_status()
            data       = resp.json()
            translated = data["responseData"]["translatedText"]
            quality    = data["responseData"]["match"]
            return SkillResult(
                success=True,
                output=f"🌐 **Translation** ({frm} → {to})\n\n{translated}\n\n_Quality: {quality:.0%}_",
                data={"translated": translated, "from": frm, "to": to},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
