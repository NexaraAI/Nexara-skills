"""
linux/process_monitor.py — Nexara Skills Warehouse
One-shot process health check — is a named process running?

Dependencies: psutil optional, falls back to pgrep
Platforms   : linux
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

class ProcessMonitorSkill(BaseSkill):
    name        = "process_monitor"
    description = (
        "Check if a process is running and get its resource usage. "
        "Args: process_name (str), action ('check'|'watch'|'restart_if_dead'), "
        "restart_cmd (str opt)."
    )
    platforms   = ["linux"]

    async def execute(self, process_name: str = "", action: str = "check", restart_cmd: str = "", **kwargs):
        if not process_name:
            return SkillResult(success=False, output="", error="process_name required.")

        rc, pids = await _run(f"pgrep -af '{process_name}'")
        is_running = rc == 0 and bool(pids.strip())

        if action == "check":
            if is_running:
                rc2, stats = await _run(f"ps -C '{process_name}' -o pid,pcpu,pmem,etime,cmd --no-header 2>/dev/null | head -5")
                return SkillResult(
                    success=True,
                    output=f"✅ `{process_name}` is **running**\n```\n{stats[:500]}\n```",
                    data={"running": True, "process": process_name},
                )
            return SkillResult(
                success=True,
                output=f"❌ `{process_name}` is **not running**",
                data={"running": False, "process": process_name},
            )

        if action == "restart_if_dead":
            if is_running:
                return SkillResult(success=True, output=f"✅ `{process_name}` is already running. No restart needed.", data={"running": True})
            if not restart_cmd:
                return SkillResult(success=False, output="", error="restart_cmd required for restart_if_dead.")
            rc2, out2 = await _run(restart_cmd + " &")
            return SkillResult(
                success=rc2 == 0,
                output=f"🔄 `{process_name}` was dead. Restarted with: `{restart_cmd}`",
                data={"restarted": True},
                error="" if rc2 == 0 else out2,
            )

        return SkillResult(success=False, output="", error=f"Unknown action: {action}")
