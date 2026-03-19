"""
android/screen_capture.py — Nexara Skills Warehouse
Take a screenshot on Android via termux-screenshot.

Dependencies: none
Platforms   : android
"""

import asyncio
from datetime import datetime
from pathlib import Path
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=20):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class ScreenCaptureSkill(BaseSkill):
    name        = "screen_capture"
    description = "Take a screenshot of the Android screen. Returns the file path."
    platforms   = ["android"]

    async def execute(self, **kwargs):
        out_dir  = Path.home() / "nexara_captures"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = out_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        rc, out  = await _run(f"termux-screenshot -f '{filename}'")
        if rc == 0 and filename.exists():
            return SkillResult(
                success=True,
                output=f"📸 Screenshot saved to `{filename}`",
                data={"path": str(filename)},
            )
        return SkillResult(success=False, output="", error=out or "Screenshot failed")
