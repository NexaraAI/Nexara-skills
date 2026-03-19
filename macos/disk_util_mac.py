"""
macos/disk_util_mac.py — Nexara Skills Warehouse
macOS disk information and APFS volume management via diskutil.

Dependencies: none (macOS built-in)
Platforms   : macos
"""

import asyncio
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

class DiskUtilMacSkill(BaseSkill):
    name        = "disk_util_mac"
    description = "macOS disk and volume information. Args: action ('list'|'info'), disk (str opt, e.g. 'disk0')."
    platforms   = ["macos"]

    async def execute(self, action: str = "list", disk: str = "", **kwargs):
        if action == "list":
            rc, out = await _run("diskutil list")
        elif action == "info":
            target = disk or "/"
            rc, out = await _run(f"diskutil info {target}")
        else:
            return SkillResult(success=False, output="", error=f"Unknown action: {action}")
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"💿 **diskutil {action}{(' '+disk) if disk else ''}**\n```\n{out[:2000]}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)
