"""
core/file_ops.py — Nexara Skills Warehouse
File system operations: read, write, list, search, delete, zip.

Dependencies: aiofiles
Platforms   : all
"""

import asyncio
import shutil
import time
from pathlib import Path

import aiofiles

from skills.base import BaseSkill, SkillResult

HOME = Path.home()

ALLOWED_ROOTS = [HOME, Path("/sdcard"), Path("/storage/emulated/0")]
BLOCKED_PATHS = [
    Path("/etc"), Path("/proc"), Path("/sys"), Path("/dev"),
    Path("/data/data"),
]


def _check(p: Path) -> str | None:
    resolved = p.resolve()
    for b in BLOCKED_PATHS:
        try:
            resolved.relative_to(b)
            return f"Access denied: `{p}` is a protected path."
        except ValueError:
            pass
    for root in ALLOWED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return None
        except ValueError:
            pass
    return f"Access denied: `{p}` is outside allowed directories."


def _human(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


class ReadFileSkill(BaseSkill):
    name        = "read_file"
    description = "Read the contents of a text file. Args: path, max_chars (default 4000)."
    platforms   = ["all"]

    async def execute(self, path: str = "", max_chars: int = 4000, **kwargs) -> SkillResult:
        if not path:
            return SkillResult(success=False, output="", error="No path provided.")
        p = Path(path).expanduser()
        if err := _check(p):
            return SkillResult(success=False, output="", error=err)
        if not p.exists():
            return SkillResult(success=False, output="", error=f"File not found: `{p}`")
        if not p.is_file():
            return SkillResult(success=False, output="", error=f"`{p}` is not a file.")
        try:
            async with aiofiles.open(p, "r", encoding="utf-8", errors="replace") as f:
                text = await f.read()
            trunc = len(text) > max_chars
            return SkillResult(
                success=True,
                output=text[:max_chars] + ("\n…[truncated]" if trunc else ""),
                data={"path": str(p), "size": p.stat().st_size, "truncated": trunc},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class WriteFileSkill(BaseSkill):
    name        = "write_file"
    description = "Write or append to a file. Args: path, content, mode ('w'|'a', default 'w')."
    platforms   = ["all"]

    async def execute(self, path: str = "", content: str = "", mode: str = "w", **kwargs) -> SkillResult:
        if not path:
            return SkillResult(success=False, output="", error="No path provided.")
        p = Path(path).expanduser()
        if err := _check(p):
            return SkillResult(success=False, output="", error=err)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(p, mode, encoding="utf-8") as f:
                await f.write(content)
            return SkillResult(
                success=True,
                output=f"✅ Written {_human(len(content.encode()))} to `{p}`",
                data={"path": str(p)},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class ListDirSkill(BaseSkill):
    name        = "list_dir"
    description = "List directory contents. Args: path (default '~'), show_hidden (bool)."
    platforms   = ["all"]

    async def execute(self, path: str = "~", show_hidden: bool = False, **kwargs) -> SkillResult:
        p = Path(path).expanduser()
        if err := _check(p):
            return SkillResult(success=False, output="", error=err)
        if not p.exists():
            return SkillResult(success=False, output="", error=f"Path not found: `{p}`")
        try:
            entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
            lines   = [f"📂 **`{p}`**\n"]
            for e in entries:
                if not show_hidden and e.name.startswith("."):
                    continue
                if e.is_dir():
                    lines.append(f"  📁 {e.name}/")
                else:
                    lines.append(f"  📄 {e.name}  ({_human(e.stat().st_size)})")
            lines.append(f"\n{len(lines)-1} items")
            return SkillResult(success=True, output="\n".join(lines), data={"path": str(p)})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class SearchFilesSkill(BaseSkill):
    name        = "search_files"
    description = "Search files by name pattern or content. Args: root, pattern (glob), content_query, max_results."
    platforms   = ["all"]

    async def execute(
        self,
        root:          str = "~",
        pattern:       str = "*",
        content_query: str = "",
        max_results:   int = 20,
        **kwargs,
    ) -> SkillResult:
        p = Path(root).expanduser()
        if err := _check(p):
            return SkillResult(success=False, output="", error=err)

        def _search():
            hits = []
            for f in p.rglob(pattern):
                if not f.is_file(): continue
                if content_query:
                    try:
                        if content_query.lower() in f.read_text(errors="ignore").lower():
                            hits.append(f)
                    except Exception:
                        pass
                else:
                    hits.append(f)
                if len(hits) >= max_results:
                    break
            return hits

        hits = await asyncio.to_thread(_search)
        if not hits:
            return SkillResult(success=True, output=f"🔍 No files found matching `{pattern}`.", data={})
        lines = [f"🔍 **{len(hits)} result(s)** for `{pattern}`\n"]
        for f in hits:
            lines.append(f"• `{f}` — {_human(f.stat().st_size)}")
        return SkillResult(success=True, output="\n".join(lines), data={"paths": [str(f) for f in hits]})


class DeleteFileSkill(BaseSkill):
    name        = "delete_file"
    description = "Delete a file or directory. Args: path, confirm (must be True)."
    platforms   = ["all"]

    async def execute(self, path: str = "", confirm: bool = False, **kwargs) -> SkillResult:
        if not path:
            return SkillResult(success=False, output="", error="No path provided.")
        if not confirm:
            return SkillResult(success=False, output="", error="Set confirm=true to delete.")
        p = Path(path).expanduser()
        if err := _check(p):
            return SkillResult(success=False, output="", error=err)
        if not p.exists():
            return SkillResult(success=False, output="", error=f"Not found: `{p}`")
        try:
            if p.is_dir(): shutil.rmtree(p)
            else:          p.unlink()
            return SkillResult(success=True, output=f"🗑️ Deleted `{p}`", data={})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class ZipFilesSkill(BaseSkill):
    name        = "zip_files"
    description = "Create a zip archive from a file or directory. Args: source, output (opt)."
    platforms   = ["all"]

    async def execute(self, source: str = "", output: str = "", **kwargs) -> SkillResult:
        if not source:
            return SkillResult(success=False, output="", error="No source path provided.")
        src = Path(source).expanduser()
        if err := _check(src):
            return SkillResult(success=False, output="", error=err)
        out = Path(output).expanduser() if output else src.parent / f"{src.name}_{int(time.time())}.zip"

        def _zip():
            import zipfile
            if src.is_dir():
                shutil.make_archive(str(out.with_suffix("")), "zip", str(src.parent), src.name)
            else:
                with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.write(src, src.name)
            return out if out.exists() else out.with_suffix(".zip")

        try:
            final = await asyncio.to_thread(_zip)
            sz    = _human(Path(final).stat().st_size)
            return SkillResult(
                success=True,
                output=f"🗜️ Archive created: `{final}` ({sz})",
                data={"path": str(final)},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class AnalyzeFileSkill(BaseSkill):
    name        = "analyze_file"
    description = "Analyze a file: PDF text, CSV schema, ZIP contents, image metadata, JSON structure."
    platforms   = ["all"]

    async def execute(self, path: str = "", **kwargs) -> SkillResult:
        if not path:
            return SkillResult(success=False, output="", error="No path provided.")
        p = Path(path).expanduser()
        if not p.exists():
            return SkillResult(success=False, output="", error=f"Not found: `{p}`")
        suffix = p.suffix.lower()

        if suffix == ".pdf":       return await self._pdf(p)
        if suffix in (".csv", ".tsv"): return await self._csv(p)
        if suffix in (".zip", ".tar", ".gz", ".bz2", ".xz"): return await self._archive(p)
        if suffix in (".jpg", ".jpeg", ".png", ".gif", ".webp"): return await self._image(p)
        if suffix == ".json":      return await self._json(p)

        try:
            async with aiofiles.open(p, "r", encoding="utf-8", errors="replace") as f:
                text = await f.read(8000)
            return SkillResult(
                success=True,
                output=f"📄 **{p.name}** ({_human(p.stat().st_size)})\n```\n{text[:2000]}\n```",
                data={},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

    async def _pdf(self, p: Path) -> SkillResult:
        try:
            import pdfplumber
            def _x():
                with pdfplumber.open(str(p)) as pdf:
                    pages = len(pdf.pages)
                    text  = "\n".join(pg.extract_text() or "" for pg in pdf.pages[:5])
                return pages, text
            pages, text = await asyncio.to_thread(_x)
            return SkillResult(
                success=True,
                output=f"📕 **PDF: {p.name}**\nPages: {pages} | {_human(p.stat().st_size)}\n\n{text[:3000]}",
                data={"pages": pages, "path": str(p)},
            )
        except ImportError:
            rc, out = await _run(f"pdftotext '{p}' - 2>/dev/null | head -c 3000")
            if rc == 0:
                return SkillResult(success=True, output=f"📕 **{p.name}**\n\n{out}", data={})
            return SkillResult(success=False, output="", error="Install pdfplumber: pip install pdfplumber")

    async def _csv(self, p: Path) -> SkillResult:
        import csv
        async with aiofiles.open(p, "r", encoding="utf-8", errors="replace") as f:
            raw = await f.read(65536)
        lines   = raw.splitlines()
        try:    dialect = csv.Sniffer().sniff(lines[0]) if lines else csv.excel
        except: dialect = csv.excel
        reader = csv.DictReader(lines, dialect=dialect)
        rows   = list(reader)[:5]
        cols   = reader.fieldnames or []
        preview = "\n".join(
            "  " + " | ".join(str(r.get(c, ""))[:20] for c in cols[:8])
            for r in rows
        )
        return SkillResult(
            success=True,
            output=(
                f"📊 **CSV: {p.name}**\n"
                f"Columns ({len(cols)}): `{'`, `'.join(cols[:12])}`\n"
                f"Rows: ~{len(lines)-1}\n\n**Preview:**\n```\n{preview}\n```"
            ),
            data={"columns": cols, "row_count": len(lines) - 1},
        )

    async def _archive(self, p: Path) -> SkillResult:
        def _list():
            import zipfile, tarfile
            if zipfile.is_zipfile(str(p)):
                with zipfile.ZipFile(str(p)) as zf:
                    infos = zf.infolist()
                    return [(i.filename, i.file_size) for i in infos[:30]], len(infos)
            if tarfile.is_tarfile(str(p)):
                with tarfile.open(str(p)) as tf:
                    members = tf.getmembers()
                    return [(m.name, m.size) for m in members[:30]], len(members)
            return None, 0
        names, total = await asyncio.to_thread(_list)
        if names is None:
            return SkillResult(success=False, output="", error="Unsupported archive type.")
        lines = [f"📦 **Archive: {p.name}** ({total} items)\n"]
        for name, size in names:
            lines.append(f"  • `{name}` ({_human(size)})")
        if total > 30:
            lines.append(f"  … and {total-30} more")
        return SkillResult(success=True, output="\n".join(lines), data={"total": total})

    async def _image(self, p: Path) -> SkillResult:
        def _meta():
            try:
                from PIL import Image
                with Image.open(str(p)) as img:
                    return {"size": f"{img.width}×{img.height}", "mode": img.mode, "format": img.format}
            except ImportError:
                return {}
        meta = await asyncio.to_thread(_meta)
        info = "  ".join(f"{k}: {v}" for k, v in meta.items()) if meta else "metadata unavailable"
        return SkillResult(
            success=True,
            output=f"🖼️ **Image: {p.name}**\n{info}\nSize: {_human(p.stat().st_size)}",
            data=meta,
        )

    async def _json(self, p: Path) -> SkillResult:
        import json
        async with aiofiles.open(p, "r", encoding="utf-8") as f:
            raw = await f.read(65536)
        data = json.loads(raw)
        if isinstance(data, list):
            summary = f"Array of {len(data)} items. First: {str(data[0])[:200]}"
        elif isinstance(data, dict):
            summary = f"Object with keys: {list(data.keys())[:15]}"
        else:
            summary = str(data)[:200]
        return SkillResult(
            success=True,
            output=f"📋 **JSON: {p.name}**\nType: {type(data).__name__}\n{summary}",
            data={},
        )


async def _run(cmd: str, timeout: int = 30) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, out.decode("utf-8", errors="replace").strip()
