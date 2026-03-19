"""
macos/launchctl.py — Nexara Skills Warehouse
macOS service management via launchctl.

Dependencies: none
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

class LaunchctlSkill(BaseSkill):
    name        = "launchctl"
    description = "Manage macOS launch agents/daemons. Args: action ('list'|'start'|'stop'|'restart'), service (str opt)."
    platforms   = ["macos"]

    async def execute(self, action: str = "list", service: str = "", **kwargs):
        if action == "list":
            rc, out = await _run("launchctl list | head -30")
            return SkillResult(success=rc==0, output=f"⚙️ **macOS Services (launchctl)**\n```\n{out[:2000]}\n```", data={})
        if not service:
            return SkillResult(success=False, output="", error=f"service label required for {action}")
        if action == "start":
            rc, out = await _run(f"launchctl start {service}")
        elif action == "stop":
            rc, out = await _run(f"launchctl stop {service}")
        elif action == "restart":
            await _run(f"launchctl stop {service}")
            rc, out = await _run(f"launchctl start {service}")
        else:
            return SkillResult(success=False, output="", error=f"Unknown action: {action}")
        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"⚙️ `{service}` {action}\n{out}",
            data={},
            error="" if ok else out,
        )
