"""
macos/pbclipboard.py — Nexara Skills Warehouse
macOS clipboard access via pbcopy/pbpaste.

Dependencies: none
Platforms   : macos
"""

import asyncio
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=10, input_data=None):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        stdin=asyncio.subprocess.PIPE if input_data else None)
    try:
        inp = input_data.encode() if input_data else None
        out, _ = await asyncio.wait_for(proc.communicate(input=inp), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class PbClipboardSkill(BaseSkill):
    name        = "pb_clipboard"
    description = "Read or write the macOS clipboard. Args: text (str opt — omit to read)."
    platforms   = ["macos"]

    async def execute(self, text: str = "", **kwargs):
        if text:
            rc, out = await _run("pbcopy", input_data=text)
            if rc == 0:
                return SkillResult(success=True, output=f"📋 Clipboard set: `{text[:60]}`", data={})
            return SkillResult(success=False, output="", error=out)
        rc, out = await _run("pbpaste")
        if rc == 0:
            return SkillResult(success=True, output=f"📋 Clipboard:\n{out[:2000]}", data={"text": out})
        return SkillResult(success=False, output="", error=out)
