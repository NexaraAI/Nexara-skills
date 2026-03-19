"""
core/csv_query.py — Nexara Skills Warehouse
Load, filter, and summarize CSV files.

Dependencies: none (stdlib csv) — pandas optional for advanced queries
Platforms   : all
"""

import asyncio
import csv
import io
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class CsvQuerySkill(BaseSkill):
    name        = "csv_query"
    description = (
        "Load and query a CSV file. "
        "Args: file_path (str), filter_col (str opt), filter_val (str opt), "
        "columns (list opt), limit (int, default 10), stats (bool, default False)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        file_path:  str  = "",
        filter_col: str  = "",
        filter_val: str  = "",
        columns:    list = None,
        limit:      int  = 10,
        stats:      bool = False,
        **kwargs,
    ):
        if not file_path:
            return SkillResult(success=False, output="", error="No file_path provided.")
        p = Path(file_path).expanduser()
        if not p.exists():
            return SkillResult(success=False, output="", error=f"File not found: {p}")

        def _process():
            with open(p, newline="", encoding="utf-8", errors="replace") as f:
                sample  = f.read(2048); f.seek(0)
                try:    dialect = csv.Sniffer().sniff(sample)
                except: dialect = csv.excel
                reader  = csv.DictReader(f, dialect=dialect)
                all_rows = list(reader)
            return all_rows, reader.fieldnames or []

        try:
            rows, fieldnames = await asyncio.to_thread(_process)
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        total = len(rows)
        if filter_col and filter_col in fieldnames:
            rows = [r for r in rows if filter_val.lower() in r.get(filter_col, "").lower()]

        if columns:
            columns = [c for c in columns if c in fieldnames]
        else:
            columns = fieldnames

        display_rows = rows[:limit]

        lines = [
            f"📊 **CSV: `{p.name}`**  ({total} rows, {len(fieldnames)} cols)",
            f"Columns: `{'`, `'.join(fieldnames[:10])}`"
        ]
        if filter_col:
            lines.append(f"Filter: `{filter_col}` contains `{filter_val}` → {len(rows)} matches")
        lines.append("\n```")
        header = " | ".join(c[:15] for c in columns[:6])
        lines.append(header)
        lines.append("-" * len(header))
        for row in display_rows:
            lines.append(" | ".join(str(row.get(c, ""))[:15] for c in columns[:6]))
        lines.append("```")

        if stats:
            numeric_cols = {}
            for col in fieldnames:
                vals = []
                for r in rows:
                    try: vals.append(float(r.get(col, "")))
                    except: pass
                if len(vals) > rows.__len__() * 0.3:
                    numeric_cols[col] = vals
            if numeric_cols:
                lines.append("\n**Numeric column stats:**")
                for col, vals in list(numeric_cols.items())[:4]:
                    mn = min(vals); mx = max(vals); avg = sum(vals)/len(vals)
                    lines.append(f"  `{col}`: min={mn:.2f}  max={mx:.2f}  avg={avg:.2f}")

        return SkillResult(
            success=True,
            output="\n".join(lines),
            data={"total_rows": total, "columns": fieldnames, "shown": len(display_rows)},
        )
