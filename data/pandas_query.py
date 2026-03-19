"""
data/pandas_query.py — Nexara Skills Warehouse
Load CSV/Excel files and run pandas-style queries.

Dependencies: pandas, openpyxl (for Excel)
Platforms   : all
"""

import asyncio
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class PandasQuerySkill(BaseSkill):
    name        = "pandas_query"
    description = (
        "Load a CSV or Excel file and run pandas operations. "
        "Args: file_path (str), operation ('head'|'describe'|'shape'|'query'|'columns'|'value_counts'), "
        "query_str (str opt), column (str opt), limit (int, default 10)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        file_path:  str = "",
        operation:  str = "head",
        query_str:  str = "",
        column:     str = "",
        limit:      int = 10,
        **kwargs,
    ):
        if not file_path:
            return SkillResult(success=False, output="", error="file_path required.")
        p = Path(file_path).expanduser()
        if not p.exists():
            return SkillResult(success=False, output="", error=f"File not found: {p}")

        def _process():
            try:
                import pandas as pd
            except ImportError:
                return None, "pandas not installed. Run: pip install pandas openpyxl"

            suffix = p.suffix.lower()
            if suffix in (".xlsx", ".xls"):
                df = pd.read_excel(str(p))
            else:
                df = pd.read_csv(str(p), low_memory=False)

            if operation == "head":
                return str(df.head(limit).to_string()), None
            if operation == "describe":
                return str(df.describe().to_string()), None
            if operation == "shape":
                return f"Rows: {df.shape[0]}  Columns: {df.shape[1]}", None
            if operation == "columns":
                return "\n".join(f"  {i}: {c}  ({df[c].dtype})" for i, c in enumerate(df.columns)), None
            if operation == "query":
                if not query_str:
                    return None, "query_str required for query operation."
                result = df.query(query_str)
                return f"{len(result)} rows matched:\n{result.head(limit).to_string()}", None
            if operation == "value_counts":
                if not column:
                    return None, "column required for value_counts."
                vc = df[column].value_counts().head(limit)
                return str(vc.to_string()), None
            return None, f"Unknown operation: {operation}"

        try:
            result, error = await asyncio.to_thread(_process)
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        if error:
            return SkillResult(success=False, output="", error=error)
        return SkillResult(
            success=True,
            output=f"📊 **{p.name}** — {operation}\n```\n{result[:2500]}\n```",
            data={"operation": operation},
        )
