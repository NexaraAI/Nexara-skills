"""
linux/systemd.py — Nexara Skills Warehouse
Manage systemd services and view journals.

Dependencies: none
Platforms   : linux
"""

import asyncio

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 30) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"


class SystemdServiceSkill(BaseSkill):
    name        = "systemd_service"
    description = "Manage a systemd service. Args: service (str), action ('start'|'stop'|'restart'|'status'|'enable'|'disable')."
    platforms   = ["linux"]

    ALLOWED_ACTIONS = {"start", "stop", "restart", "status", "enable", "disable"}

    async def execute(self, service: str = "", action: str = "status", **kwargs) -> SkillResult:
        if not service:
            return SkillResult(success=False, output="", error="No service specified.")
        if action not in self.ALLOWED_ACTIONS:
            return SkillResult(success=False, output="", error=f"Invalid action. Use: {self.ALLOWED_ACTIONS}")

        cmd = f"sudo systemctl {action} {service}"
        if action == "status":
            cmd = f"systemctl status {service} --no-pager -l"

        rc, out = await _run(cmd)
        ok = rc == 0 or action == "status"
        return SkillResult(
            success=ok,
            output=f"**systemctl {action} {service}**\n```\n{out[:1500]}\n```",
            data={"returncode": rc},
            error="" if ok else out[-300:],
        )


class JournalLogSkill(BaseSkill):
    name        = "journal_log"
    description = "View systemd journal logs. Args: service (str opt), lines (int, default 50), level ('err'|'warning'|'info')."
    platforms   = ["linux"]

    async def execute(
        self,
        service: str = "",
        lines:   int = 50,
        level:   str = "",
        **kwargs,
    ) -> SkillResult:
        cmd = f"journalctl -n {lines} --no-pager"
        if service: cmd += f" -u {service}"
        if level:   cmd += f" -p {level}"

        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"📋 **Journal Logs**\n```\n{out[:3000]}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)


class SystemdListSkill(BaseSkill):
    name        = "systemd_list"
    description = "List running or failed systemd services. Args: state ('running'|'failed'|'all')."
    platforms   = ["linux"]

    async def execute(self, state: str = "running", **kwargs) -> SkillResult:
        if state == "failed":
            cmd = "systemctl list-units --failed --no-pager"
        elif state == "all":
            cmd = "systemctl list-units --no-pager | head -40"
        else:
            cmd = "systemctl list-units --state=running --no-pager | head -30"

        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"⚙️ **Services ({state})**\n```\n{out[:2000]}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)
