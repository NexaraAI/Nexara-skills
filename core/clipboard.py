"""
core/clipboard.py — Nexara Skills Warehouse
Platform-aware clipboard read and write.
Detects environment and uses the appropriate backend.

Dependencies: none (pyperclip optional)
Platforms   : all
"""

import asyncio
import os
import sys

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 10) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"


async def _read_clipboard() -> str | None:
    # Termux
    if os.path.exists("/data/data/com.termux"):
        rc, out = await _run("termux-clipboard-get")
        return out if rc == 0 else None
    # macOS
    if sys.platform == "darwin":
        rc, out = await _run("pbpaste")
        return out if rc == 0 else None
    # Linux (X11 / Wayland)
    if sys.platform.startswith("linux"):
        rc, out = await _run("xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null || wl-paste 2>/dev/null")
        return out if rc == 0 else None
    # Windows
    if sys.platform == "win32":
        rc, out = await _run("powershell -command Get-Clipboard")
        return out if rc == 0 else None
    return None


async def _write_clipboard(text: str) -> bool:
    # Termux
    if os.path.exists("/data/data/com.termux"):
        proc = await asyncio.create_subprocess_shell(
            "termux-clipboard-set",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate(text.encode())
        return proc.returncode == 0
    # macOS
    if sys.platform == "darwin":
        proc = await asyncio.create_subprocess_shell(
            "pbcopy", stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate(text.encode())
        return proc.returncode == 0
    # Linux
    if sys.platform.startswith("linux"):
        for cmd in [
            f"echo '{text}' | xclip -selection clipboard",
            f"echo '{text}' | xsel --clipboard --input",
            f"echo '{text}' | wl-copy",
        ]:
            rc, _ = await _run(cmd)
            if rc == 0: return True
    # Windows
    if sys.platform == "win32":
        rc, _ = await _run(f'powershell -command "Set-Clipboard -Value \'{text}\'"')
        return rc == 0
    return False


class ClipboardReadSkill(BaseSkill):
    name        = "clipboard_read"
    description = "Read the current clipboard contents."
    platforms   = ["all"]

    async def execute(self, **kwargs) -> SkillResult:
        content = await _read_clipboard()
        if content is None:
            return SkillResult(
                success=False, output="",
                error="Could not read clipboard. No clipboard tool available.",
            )
        if not content:
            return SkillResult(success=True, output="📋 Clipboard is empty.", data={})
        return SkillResult(
            success=True,
            output=f"📋 **Clipboard contents:**\n\n{content[:2000]}",
            data={"content": content, "length": len(content)},
        )


class ClipboardWriteSkill(BaseSkill):
    name        = "clipboard_write"
    description = "Write text to the clipboard. Args: text (str)."
    platforms   = ["all"]

    async def execute(self, text: str = "", **kwargs) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        ok = await _write_clipboard(text)
        if ok:
            preview = text[:60] + ("…" if len(text) > 60 else "")
            return SkillResult(
                success=True,
                output=f"📋 Copied to clipboard: `{preview}`",
                data={"length": len(text)},
            )
        return SkillResult(
            success=False, output="",
            error="Could not write to clipboard. No clipboard tool available.",
        )
