"""
core/text_diff.py — Nexara Skills Warehouse
Diff two texts or files line by line.

Dependencies: none (stdlib difflib)
Platforms   : all
"""

import difflib
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class TextDiffSkill(BaseSkill):
    name        = "text_diff"
    description = (
        "Show the diff between two texts or files. "
        "Args: text_a (str), text_b (str), file_a (str opt), file_b (str opt), context (int, default 3)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        text_a:  str = "",
        text_b:  str = "",
        file_a:  str = "",
        file_b:  str = "",
        context: int = 3,
        **kwargs,
    ):
        if file_a:
            try: text_a = Path(file_a).expanduser().read_text(encoding="utf-8", errors="replace")
            except Exception as exc: return SkillResult(success=False, output="", error=str(exc))
        if file_b:
            try: text_b = Path(file_b).expanduser().read_text(encoding="utf-8", errors="replace")
            except Exception as exc: return SkillResult(success=False, output="", error=str(exc))

        if not text_a or not text_b:
            return SkillResult(success=False, output="", error="Provide text_a and text_b (or file_a and file_b).")

        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        label_a = file_a or "text_a"
        label_b = file_b or "text_b"

        diff = list(difflib.unified_diff(lines_a, lines_b, fromfile=label_a, tofile=label_b, n=context))
        if not diff:
            return SkillResult(success=True, output="✅ No differences found — texts are identical.", data={"identical": True})

        diff_text = "".join(diff)[:3000]
        added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
        return SkillResult(
            success=True,
            output=f"📊 **Diff** (+{added} lines, -{removed} lines)\n```diff\n{diff_text}\n```",
            data={"added": added, "removed": removed},
        )
