"""
macos/screen_capture_mac.py — Nexara Skills Warehouse
Screenshot on macOS using the screencapture CLI tool.

Dependencies: none (macOS built-in)
Platforms   : macos
"""

import asyncio
from datetime import datetime
from pathlib import Path
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=15):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class ScreenCaptureMacSkill(BaseSkill):
    name        = "screen_capture_mac"
    description = "Take a screenshot on macOS. Args: window_only (bool), include_cursor (bool)."
    platforms   = ["macos"]

    async def execute(self, window_only: bool = False, include_cursor: bool = False, **kwargs):
        out_dir  = Path.home() / "nexara_captures"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = out_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        flags    = []
        if window_only:   flags.append("-w")
        if include_cursor: flags.append("-C")
        cmd = f"screencapture {' '.join(flags)} '{filename}'"
        rc, out = await _run(cmd)
        if rc == 0 and filename.exists():
            return SkillResult(
                success=True,
                output=f"📸 Screenshot saved to `{filename}`",
                data={"path": str(filename)},
            )
        return SkillResult(success=False, output="", error=out or "screencapture failed")
