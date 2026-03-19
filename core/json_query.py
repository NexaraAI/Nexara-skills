"""
core/json_query.py — Nexara Skills Warehouse
Parse and query JSON data with dot-notation and basic filtering.

Dependencies: none (stdlib json)
Platforms   : all
"""

import json
import re
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class JsonQuerySkill(BaseSkill):
    name        = "json_query"
    description = (
        "Parse and query JSON data. "
        "Args: data (str JSON), file_path (str opt), query (str, dot-notation e.g. 'users.0.name'), "
        "pretty (bool, default False)."
    )
    platforms   = ["all"]

    async def execute(self, data: str = "", file_path: str = "", query: str = "", pretty: bool = False, **kwargs):
        if file_path:
            p = Path(file_path).expanduser()
            if not p.exists():
                return SkillResult(success=False, output="", error=f"File not found: {p}")
            data = p.read_text(encoding="utf-8")

        if not data:
            return SkillResult(success=False, output="", error="No JSON data provided.")

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as exc:
            return SkillResult(success=False, output="", error=f"Invalid JSON: {exc}")

        if query:
            parts = re.split(r"[\.\[\]]", query)
            parts = [p for p in parts if p]
            current = parsed
            try:
                for part in parts:
                    if isinstance(current, list):
                        current = current[int(part)]
                    elif isinstance(current, dict):
                        current = current[part]
                    else:
                        raise KeyError(f"Cannot access '{part}' on {type(current).__name__}")
                parsed = current
            except (KeyError, IndexError, ValueError) as exc:
                return SkillResult(success=False, output="", error=f"Query failed: {exc}")

        output_str = json.dumps(parsed, indent=2 if pretty else None, ensure_ascii=False)[:3000]
        kind       = type(parsed).__name__
        summary    = f"Type: {kind}"
        if isinstance(parsed, list):   summary += f"  Items: {len(parsed)}"
        if isinstance(parsed, dict):   summary += f"  Keys: {list(parsed.keys())[:8]}"

        return SkillResult(
            success=True,
            output=f"📋 **JSON Query**  _{summary}_\n```json\n{output_str}\n```",
            data={"type": kind, "result": parsed},
        )
