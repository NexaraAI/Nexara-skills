"""
windows/powershell.py — Nexara Skills Warehouse
Run PowerShell commands and scripts on Windows.

Dependencies: none
Platforms   : windows
"""

import asyncio
import shlex

from skills.base import BaseSkill, SkillResult

TIMEOUT = 30

_BLOCKED = [
    "Format-Volume", "Remove-Item /", "Remove-Item C:\\",
    "Stop-Computer", "Restart-Computer",
    "Clear-Disk", "Initialize-Disk",
]


async def _run_ps(command: str, timeout: int = TIMEOUT) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        f'powershell -NoProfile -NonInteractive -Command "{command}"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Timed out after {timeout}s"


class PowerShellSkill(BaseSkill):
    name        = "powershell"
    description = "Run a PowerShell command on Windows. Args: command (str)."
    platforms   = ["windows"]

    async def execute(self, command: str = "", **kwargs) -> SkillResult:
        if not command:
            return SkillResult(success=False, output="", error="No command provided.")
        for pattern in _BLOCKED:
            if pattern.lower() in command.lower():
                return SkillResult(success=False, output="", error=f"Blocked: `{pattern}`")
        rc, out = await _run_ps(command)
        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"```\n{out[:2000]}\n```" if out else "(no output)",
            data={"returncode": rc},
            error="" if ok else out[-300:],
        )


class WinProcessListSkill(BaseSkill):
    name        = "win_process_list"
    description = "List running Windows processes sorted by CPU or memory. Args: sort_by ('cpu'|'mem'), limit (int)."
    platforms   = ["windows"]

    async def execute(self, sort_by: str = "cpu", limit: int = 15, **kwargs) -> SkillResult:
        sort_prop = "WorkingSet" if sort_by == "mem" else "CPU"
        cmd = (
            f"Get-Process | Sort-Object -{sort_prop} | "
            f"Select-Object -First {limit} Name,Id,CPU,WorkingSet | "
            "Format-Table -AutoSize"
        )
        rc, out = await _run_ps(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"🔄 **Processes (by {sort_by})**\n```\n{out[:2000]}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)


class WingetInstallSkill(BaseSkill):
    name        = "winget_install"
    description = "Install a package via winget (Windows Package Manager). Args: package (str)."
    platforms   = ["windows"]

    async def execute(self, package: str = "", **kwargs) -> SkillResult:
        if not package:
            return SkillResult(success=False, output="", error="No package specified.")
        proc = await asyncio.create_subprocess_shell(
            f'winget install --accept-source-agreements --accept-package-agreements -e --id {package}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            output = out.decode("utf-8", errors="replace").strip()
            rc     = proc.returncode
            if rc == 0:
                return SkillResult(success=True, output=f"✅ Installed `{package}`.", data={})
            return SkillResult(success=False, output="", error=output[-300:])
        except asyncio.TimeoutError:
            proc.kill()
            return SkillResult(success=False, output="", error="Install timed out.")
