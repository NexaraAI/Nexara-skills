"""
android/camera.py — Nexara Skills Warehouse
Camera capture via Termux:API. Photo is auto-sent to Telegram by main.py.

Dependencies: none
Platforms   : android
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 30) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Camera timed out"


class CameraSkill(BaseSkill):
    name        = "camera_capture"
    description = "Take a photo with the device camera. Returns the file path."
    platforms   = ["android"]

    async def execute(self, camera_id: int = 0, **kwargs) -> SkillResult:
        out_dir = Path.home() / "nexara_captures"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = out_dir / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        rc, out = await _run(f"termux-camera-photo -c {camera_id} '{filename}'")
        if rc == 0 and filename.exists():
            return SkillResult(
                success=True,
                output=f"📷 Photo saved to `{filename}`",
                data={"path": str(filename)},
            )
        return SkillResult(success=False, output="", error=out or "Camera capture failed")
