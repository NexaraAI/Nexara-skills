"""
windows/windows_services.py — Nexara Skills Warehouse
Manage Windows services via sc.exe and net.exe.

Dependencies: none
Platforms   : windows
"""

import asyncio
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

class WindowsServicesSkill(BaseSkill):
    name        = "windows_services"
    description = "Manage Windows services. Args: action ('list'|'status'|'start'|'stop'|'restart'), service (str opt)."
    platforms   = ["windows"]

    async def execute(self, action: str = "list", service: str = "", **kwargs):
        if action == "list":
            rc, out = await _run("sc query type= all state= all | findstr /i /c:"SERVICE_NAME" /c:"STATE"")
            return SkillResult(success=rc==0, output=f"⚙️ **Windows Services**\n```\n{out[:2000]}\n```", data={})
        if not service:
            return SkillResult(success=False, output="", error=f"service name required for {action}")
        if action == "status":
            rc, out = await _run(f"sc query "{service}"")
        elif action == "start":
            rc, out = await _run(f"net start "{service}"")
        elif action == "stop":
            rc, out = await _run(f"net stop "{service}"")
        elif action == "restart":
            await _run(f"net stop "{service}"")
            rc, out = await _run(f"net start "{service}"")
        else:
            return SkillResult(success=False, output="", error=f"Unknown action: {action}")
        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"⚙️ **{service}** {action}\n```\n{out[:1000]}\n```",
            data={"returncode": rc},
            error="" if ok else out[-200:],
        )
