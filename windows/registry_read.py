"""
windows/registry_read.py — Nexara Skills Warehouse
Read Windows Registry keys via PowerShell.

Dependencies: none
Platforms   : windows
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

class RegistryReadSkill(BaseSkill):
    name        = "registry_read"
    description = "Read a Windows Registry key. Args: key (str, e.g. 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion'), value_name (str opt)."
    platforms   = ["windows"]

    async def execute(self, key: str = "", value_name: str = "", **kwargs):
        if not key:
            return SkillResult(success=False, output="", error="key path required.")
        if value_name:
            cmd = f"powershell -NoProfile -Command "(Get-ItemProperty -Path '{key}' -Name '{value_name}').'{value_name}'""
        else:
            cmd = f"powershell -NoProfile -Command "Get-ItemProperty -Path '{key}' | Format-List""
        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"🗝️ **Registry: `{key}`**\n```\n{out[:2000]}\n```",
                data={"key": key},
            )
        return SkillResult(success=False, output="", error=out)
