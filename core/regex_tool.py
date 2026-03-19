"""
core/regex_tool.py — Nexara Skills Warehouse
Test, find, and replace with regular expressions.

Dependencies: none (stdlib re)
Platforms   : all
"""

import re
from skills.base import BaseSkill, SkillResult


class RegexToolSkill(BaseSkill):
    name        = "regex_tool"
    description = (
        "Test a regex pattern against text. "
        "Args: pattern (str), text (str), mode ('match'|'findall'|'replace'), "
        "replacement (str, for replace mode), flags ('i'|'m'|'s' opt)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        pattern:     str = "",
        text:        str = "",
        mode:        str = "findall",
        replacement: str = "",
        flags:       str = "",
        **kwargs,
    ):
        if not pattern or not text:
            return SkillResult(success=False, output="", error="pattern and text are required.")

        re_flags = 0
        if "i" in flags: re_flags |= re.IGNORECASE
        if "m" in flags: re_flags |= re.MULTILINE
        if "s" in flags: re_flags |= re.DOTALL

        try:
            compiled = re.compile(pattern, re_flags)
        except re.error as exc:
            return SkillResult(success=False, output="", error=f"Invalid regex: {exc}")

        if mode == "match":
            m = compiled.match(text)
            if m:
                groups = m.groups()
                return SkillResult(
                    success=True,
                    output=f"✅ **Match found**\nFull match: `{m.group(0)}`\nGroups: {groups}",
                    data={"matched": True, "groups": list(groups)},
                )
            return SkillResult(success=True, output="❌ No match found.", data={"matched": False})

        if mode == "findall":
            matches = compiled.findall(text)
            if not matches:
                return SkillResult(success=True, output="❌ No matches found.", data={"matches": []})
            preview = "\n".join(f"  • `{m}`" for m in matches[:20])
            return SkillResult(
                success=True,
                output=f"✅ **{len(matches)} match(es)**\n\n{preview}",
                data={"matches": matches},
            )

        if mode == "replace":
            result  = compiled.sub(replacement, text)
            changes = len(compiled.findall(text))
            return SkillResult(
                success=True,
                output=f"✅ **Replaced {changes} occurrence(s)**\n\n{result[:1000]}",
                data={"result": result, "changes": changes},
            )

        return SkillResult(success=False, output="", error=f"Unknown mode: {mode}")
