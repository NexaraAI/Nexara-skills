"""
core/download.py — Nexara Skills Warehouse
Download anything: HTTP/HTTPS files, YouTube/video via yt-dlp, APKs.

Dependencies: httpx, aiofiles
Optional    : yt-dlp (auto-installed if missing)
Platforms   : all
"""

import asyncio
import logging
import mimetypes
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import aiofiles
import httpx

from skills.base import BaseSkill, SkillResult

logger = logging.getLogger("nexara.skill.download")

DOWNLOADS_DIR  = Path.home() / "nexara_downloads"
CHUNK_SIZE     = 256 * 1024
MAX_SIZE_BYTES = 2 * 1024 ** 3
MAX_CONCURRENT = asyncio.Semaphore(3)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    )
}

VIDEO_DOMAINS = {
    "youtube.com", "youtu.be", "vimeo.com", "dailymotion.com",
    "twitch.tv", "tiktok.com", "instagram.com", "twitter.com",
    "x.com", "reddit.com", "facebook.com", "rumble.com",
}


def _human(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def _safe_name(url: str, cd: str = "") -> str:
    if cd:
        m = re.search(r'filename\*?=["\'']?(?:UTF-8\'\')?([^"\';\n]+)', cd)
        if m: return unquote(m.group(1).strip())
    name = Path(unquote(urlparse(url).path)).name
    return name or f"download_{int(time.time())}"


def _is_video(url: str) -> bool:
    host = urlparse(url).netloc.lower().lstrip("www.")
    return any(d in host for d in VIDEO_DOMAINS) or any(d in url for d in VIDEO_DOMAINS)


async def _run(cmd: str, timeout: int = 600) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, out.decode("utf-8", errors="replace").strip()


class DownloadSkill(BaseSkill):
    name        = "download"
    description = (
        "Download any file: HTTP/HTTPS, YouTube/video, APK, audio. "
        "Args: url, filename (opt), subdir (opt), audio_only (bool), "
        "quality ('best'/'worst'), install_apk (bool)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        url:         str  = "",
        filename:    str  = "",
        subdir:      str  = "",
        audio_only:  bool = False,
        quality:     str  = "best",
        install_apk: bool = False,
        **kwargs,
    ) -> SkillResult:
        if not url:
            return SkillResult(success=False, output="", error="No URL provided.")

        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        save_dir = DOWNLOADS_DIR / subdir if subdir else DOWNLOADS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)

        async with MAX_CONCURRENT:
            if _is_video(url):
                result = await self._yt_dlp(url, save_dir, quality, audio_only, filename)
            else:
                result = await self._http(url, save_dir, filename)

        if result.success and install_apk:
            path = result.data.get("path", "")
            if path.endswith(".apk"):
                rc, out = await _run(f"pm install -r '{path}'")
                suffix  = "\n📦 APK installed." if rc == 0 else f"\n⚠️ APK install failed: {out[:80]}"
                result.output += suffix

        return result

    async def _http(self, url: str, save_dir: Path, override: str) -> SkillResult:
        try:
            async with httpx.AsyncClient(
                headers=HEADERS, follow_redirects=True,
                timeout=httpx.Timeout(connect=15, read=300, write=60, pool=15),
            ) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    cd    = resp.headers.get("content-disposition", "")
                    name  = override or _safe_name(url, cd)
                    if not Path(name).suffix:
                        ct  = resp.headers.get("content-type", "").split(";")[0].strip()
                        ext = mimetypes.guess_extension(ct) or ""
                        name += ext
                    save_path = save_dir / name
                    if save_path.exists():
                        save_path = save_dir / f"{save_path.stem}_{int(time.time())}{save_path.suffix}"
                    total    = int(resp.headers.get("content-length", 0))
                    received = 0
                    t0       = time.time()
                    if total and total > MAX_SIZE_BYTES:
                        return SkillResult(success=False, output="", error=f"File too large: {_human(total)}")
                    async with aiofiles.open(save_path, "wb") as f:
                        async for chunk in resp.aiter_bytes(CHUNK_SIZE):
                            await f.write(chunk)
                            received += len(chunk)

            elapsed = time.time() - t0
            speed   = received / elapsed if elapsed > 0 else 0
            mime    = resp.headers.get("content-type", "?").split(";")[0]
            return SkillResult(
                success=True,
                output=(
                    f"✅ **Downloaded**\n"
                    f"📄 `{name}`\n📁 `{save_path}`\n"
                    f"📦 {_human(received)}  ·  {_human(int(speed))}/s  ·  {elapsed:.1f}s\n"
                    f"🏷️  {mime}"
                ),
                data={"path": str(save_path), "size": received, "name": name},
            )
        except httpx.HTTPStatusError as exc:
            return SkillResult(success=False, output="", error=f"HTTP {exc.response.status_code}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

    async def _yt_dlp(self, url, save_dir, quality, audio_only, filename) -> SkillResult:
        rc, _ = await _run("yt-dlp --version")
        if rc != 0:
            rc2, _ = await _run("pip install -q yt-dlp", timeout=120)
            if rc2 != 0:
                return SkillResult(success=False, output="", error="yt-dlp install failed.")
        fmt  = "-x --audio-format mp3" if audio_only else f"-f {quality}"
        tmpl = str(save_dir / (f"{filename}.%(ext)s" if filename else "%(title)s.%(ext)s"))
        cmd  = f'yt-dlp {fmt} -o "{tmpl}" --no-playlist "{url}"'
        rc, out = await _run(cmd)
        if rc == 0:
            dest = re.search(r'\[Merger\] Merging formats into "(.+?)"', out)
            if not dest:
                dest = re.search(r"\[download\] Destination: (.+)", out)
            path = dest.group(1).strip() if dest else str(save_dir)
            return SkillResult(
                success=True,
                output=f"✅ **Video downloaded**\n📁 `{path}`",
                data={"path": path},
            )
        return SkillResult(success=False, output="", error=out[-500:])


class ListDownloadsSkill(BaseSkill):
    name        = "list_downloads"
    description = "List all files in the Nexara downloads folder."
    platforms   = ["all"]

    async def execute(self, subdir: str = "", **kwargs) -> SkillResult:
        target = DOWNLOADS_DIR / subdir if subdir else DOWNLOADS_DIR
        target.mkdir(parents=True, exist_ok=True)
        files = sorted(
            (f for f in target.rglob("*") if f.is_file()),
            key=lambda f: f.stat().st_mtime, reverse=True
        )[:50]
        if not files:
            return SkillResult(success=True, output="📁 Downloads folder is empty.", data={})
        total = sum(f.stat().st_size for f in files)
        lines = [f"📁 **Downloads** (`{target}`)\n"]
        for f in files:
            lines.append(f"• `{f.name}` — {_human(f.stat().st_size)}")
        lines.append(f"\n**Total:** {_human(total)} in {len(files)} files")
        return SkillResult(success=True, output="\n".join(lines), data={"count": len(files)})
