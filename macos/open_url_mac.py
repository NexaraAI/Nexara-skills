"""
macos/open_url_mac.py — Nexara Skills Warehouse
Open URLs or files with the default application on macOS.

Dependencies: none
Platforms   : macos
"""

import asyncio
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=10):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class OpenUrlMacSkill(BaseSkill):
    name        = "open_url_mac"
    description = "Open a URL or file with the default app on macOS. Args: target (str URL or path), app (str opt)."
    platforms   = ["macos"]

    async def execute(self, target: str = "", app: str = "", **kwargs):
        if not target:
            return SkillResult(success=False, output="", error="No target provided.")
        cmd = f"open {('-a \"'+app+'\"') if app else ''} '{target}'"
        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(success=True, output=f"🔗 Opened `{target}`{(' in '+app) if app else ''}", data={})
        return SkillResult(success=False, output="", error=out)
