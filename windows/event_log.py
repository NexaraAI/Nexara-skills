"""
windows/event_log.py — Nexara Skills Warehouse
Read Windows Event Log entries.

Dependencies: none
Platforms   : windows
"""

import asyncio
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=30):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class EventLogSkill(BaseSkill):
    name        = "event_log"
    description = "Read Windows Event Log. Args: log ('System'|'Application'|'Security'), level ('Error'|'Warning'|'Information'), limit (int, default 10)."
    platforms   = ["windows"]

    async def execute(self, log: str = "System", level: str = "Error", limit: int = 10, **kwargs):
        limit  = max(1, min(50, limit))
        cmd    = (
            f"powershell -NoProfile -Command ""
            f"Get-EventLog -LogName {log} -EntryType {level} -Newest {limit} "
            f"| Select-Object TimeGenerated,Source,Message "
            f"| Format-List"
            f"""
        )
        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"📋 **Event Log: {log} ({level})**\n```\n{out[:2500]}\n```",
                data={"log": log, "level": level},
            )
        return SkillResult(success=False, output="", error=out)
