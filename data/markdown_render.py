"""
data/markdown_render.py — Nexara Skills Warehouse
Convert Markdown to HTML and save or return it.

Dependencies: markdown (pip install markdown)
Platforms   : all
"""

import asyncio
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class MarkdownRenderSkill(BaseSkill):
    name        = "markdown_render"
    description = (
        "Convert Markdown text to HTML. "
        "Args: text (str opt), file_path (str opt), output_path (str opt), "
        "return_html (bool, default False)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        text:        str  = "",
        file_path:   str  = "",
        output_path: str  = "",
        return_html: bool = False,
        **kwargs,
    ):
        def _convert():
            try:
                import markdown
            except ImportError:
                return None, "markdown not installed. Run: pip install markdown"

            if file_path:
                p = Path(file_path).expanduser()
                if not p.exists():
                    return None, f"File not found: {p}"
                md_text = p.read_text(encoding="utf-8")
            elif text:
                md_text = text
            else:
                return None, "text or file_path required."

            html     = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
            full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{font-family:sans-serif;max-width:800px;margin:2em auto;line-height:1.6}}pre{{background:#f4f4f4;padding:1em;border-radius:4px}}code{{background:#f4f4f4;padding:2px 4px}}</style></head><body>{html}</body></html>"

            if output_path:
                out = Path(output_path).expanduser()
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(full_html, encoding="utf-8")
                return f"✅ Rendered to `{out}` ({len(full_html)} bytes)", None
            if return_html:
                return full_html[:3000], None
            # Default: show text preview
            word_count = len(md_text.split())
            return f"✅ Converted {word_count} words → {len(html)} bytes HTML.\nAdd output_path to save, or return_html=true to get HTML.", None

        try:
            result, error = await asyncio.to_thread(_convert)
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        if error:
            return SkillResult(success=False, output="", error=error)
        return SkillResult(success=True, output=result, data={})
