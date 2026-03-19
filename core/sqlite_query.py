"""
core/sqlite_query.py — Nexara Skills Warehouse
Query any SQLite database file.

Dependencies: none (stdlib sqlite3)
Platforms   : all
"""

import asyncio
import sqlite3
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class SqliteQuerySkill(BaseSkill):
    name        = "sqlite_query"
    description = (
        "Run a SQL query on a SQLite database file. "
        "Args: db_path (str), query (str), list_tables (bool, default False), limit (int, default 20)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        db_path:     str  = "",
        query:       str  = "",
        list_tables: bool = False,
        limit:       int  = 20,
        **kwargs,
    ):
        if not db_path:
            return SkillResult(success=False, output="", error="No db_path provided.")
        p = Path(db_path).expanduser()
        if not p.exists():
            return SkillResult(success=False, output="", error=f"Database not found: {p}")

        def _run():
            with sqlite3.connect(str(p)) as conn:
                conn.row_factory = sqlite3.Row
                if list_tables or not query:
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    ).fetchall()
                    return "tables", [t["name"] for t in tables]
                rows = conn.execute(query).fetchmany(limit)
                cols = [d[0] for d in conn.execute(query).description] if rows else []
                return "rows", (rows, cols)

        try:
            kind, result = await asyncio.to_thread(_run)
        except sqlite3.Error as exc:
            return SkillResult(success=False, output="", error=f"SQL error: {exc}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        if kind == "tables":
            if not result:
                return SkillResult(success=True, output=f"📋 `{p.name}` — no tables found.", data={})
            lines = [f"📋 **Tables in `{p.name}`** ({len(result)})\n"]
            for t in result:
                lines.append(f"  • `{t}`")
            return SkillResult(success=True, output="\n".join(lines), data={"tables": result})

        rows, cols = result
        if not rows:
            return SkillResult(success=True, output="Query returned 0 rows.", data={"rows": 0})

        lines   = [f"📋 **Query Result** ({len(rows)} rows)\n```"]
        header  = " | ".join(c[:12] for c in cols[:6])
        lines.append(header)
        lines.append("-" * len(header))
        for row in rows:
            lines.append(" | ".join(str(row[i])[:12] for i in range(min(6, len(cols)))))
        lines.append("```")
        return SkillResult(success=True, output="\n".join(lines), data={"rows": len(rows), "cols": cols})
