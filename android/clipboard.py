"""
android/clipboard.py — Nexara Skills Warehouse
Read and write Android clipboard via Termux:API.

Dependencies: none
Platforms   : android
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

class ClipboardSkill(BaseSkill):
    name        = "clipboard"
    description = "Read or write the Android clipboard. Args: text (str opt — omit to read)."
    platforms   = ["android"]

    async def execute(self, text: str = "", **kwargs):
        if text:
            rc, out = await _run(f"termux-clipboard-set '{text}'")
            if rc == 0:
                return SkillResult(success=True, output=f"📋 Clipboard set: `{text[:60]}`", data={})
            return SkillResult(success=False, output="", error=out)
        rc, out = await _run("termux-clipboard-get")
        if rc == 0:
            return SkillResult(success=True, output=f"📋 Clipboard:\n{out[:1000]}", data={"text": out})
        return SkillResult(success=False, output="", error=out)
