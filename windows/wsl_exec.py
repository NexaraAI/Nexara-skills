"""
windows/wsl_exec.py — Nexara Skills Warehouse
Run commands inside WSL (Windows Subsystem for Linux) from Windows.

Dependencies: WSL installed
Platforms   : windows
"""

import asyncio
from skills.base import BaseSkill, SkillResult

BLOCKED = ["rm -rf /", "mkfs", "shutdown", "reboot"]

async def _run(cmd, timeout=30):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class WslExecSkill(BaseSkill):
    name        = "wsl_exec"
    description = "Run a bash command inside WSL from Windows. Args: command (str), distro (str opt, e.g. 'Ubuntu')."
    platforms   = ["windows"]

    async def execute(self, command: str = "", distro: str = "", **kwargs):
        if not command:
            return SkillResult(success=False, output="", error="No command provided.")
        for pattern in BLOCKED:
            if pattern in command:
                return SkillResult(success=False, output="", error=f"Blocked: `{pattern}`")
        distro_flag = f"-d {distro}" if distro else ""
        cmd = f"wsl {distro_flag} -- bash -c "{command}""
        rc, out = await _run(cmd)
        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"🐧 **WSL**{(' ('+distro+')') if distro else ''}\n```\n{out[:2000]}\n```",
            data={"returncode": rc},
            error="" if ok else out[-200:],
        )
