"""
data/sqlite_manager.py — Nexara Skills Warehouse
Create, manage, and export SQLite databases.

Dependencies: none (stdlib sqlite3)
Platforms   : all
"""

import asyncio
import csv
import io
import json
import sqlite3
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class SqliteManagerSkill(BaseSkill):
    name        = "sqlite_manager"
    description = (
        "Manage SQLite databases: create tables, insert, update, delete, export. "
        "Args: db_path (str), action ('execute'|'create_table'|'export_csv'|'export_json'|'tables'|'schema'), "
        "query (str opt), table (str opt)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        db_path:  str = "",
        action:   str = "tables",
        query:    str = "",
        table:    str = "",
        **kwargs,
    ):
        if not db_path:
            return SkillResult(success=False, output="", error="db_path required.")
        p = Path(db_path).expanduser()

        def _work():
            with sqlite3.connect(str(p)) as conn:
                conn.row_factory = sqlite3.Row

                if action == "tables":
                    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                    return "ok", "\n".join(f"  • `{r['name']}`" for r in rows) or "No tables."

                if action == "schema":
                    if not table:
                        return "err", "table required for schema."
                    rows = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
                    lines = ["\n".join(f"  {r['name']} {r['type']} {'NOT NULL' if r['notnull'] else ''}" for r in rows)]
                    return "ok", "\n".join(lines)

                if action == "execute":
                    if not query:
                        return "err", "query required."
                    if query.strip().upper().startswith(("INSERT","UPDATE","DELETE","CREATE","DROP","ALTER")):
                        conn.execute(query)
                        conn.commit()
                        return "ok", f"✅ Executed: `{query[:80]}`"
                    rows  = conn.execute(query).fetchmany(50)
                    cols  = [d[0] for d in conn.execute(query).description]
                    lines = [" | ".join(cols[:6])]
                    lines.append("-" * len(lines[0]))
                    for row in rows:
                        lines.append(" | ".join(str(row[i])[:15] for i in range(min(6, len(cols)))))
                    return "ok", f"```\n" + "\n".join(lines) + "\n```"

                if action == "export_csv":
                    if not table:
                        return "err", "table required for export_csv."
                    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                    cols = [d[0] for d in conn.execute(f"SELECT * FROM {table}").description]
                    buf  = io.StringIO()
                    writer = csv.writer(buf)
                    writer.writerow(cols)
                    writer.writerows(rows)
                    out_path = p.parent / f"{table}.csv"
                    out_path.write_text(buf.getvalue(), encoding="utf-8")
                    return "ok", f"✅ Exported `{table}` → `{out_path}` ({len(rows)} rows)"

                if action == "export_json":
                    if not table:
                        return "err", "table required for export_json."
                    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                    data = [dict(r) for r in rows]
                    out_path = p.parent / f"{table}.json"
                    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    return "ok", f"✅ Exported `{table}` → `{out_path}` ({len(data)} records)"

                return "err", f"Unknown action: {action}"

        try:
            status, result = await asyncio.to_thread(_work)
        except sqlite3.Error as exc:
            return SkillResult(success=False, output="", error=f"SQL error: {exc}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        if status == "err":
            return SkillResult(success=False, output="", error=result)
        return SkillResult(
            success=True,
            output=f"🗄️ **SQLite: `{p.name}`** — {action}\n{result}",
            data={"action": action, "db": str(p)},
        )
