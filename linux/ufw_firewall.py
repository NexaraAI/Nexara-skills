"""
linux/ufw_firewall.py — Nexara Skills Warehouse
UFW (Uncomplicated Firewall) management.

Dependencies: ufw
Platforms   : linux
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

class UfwFirewallSkill(BaseSkill):
    name        = "ufw_firewall"
    description = (
        "Manage UFW firewall rules. "
        "Args: action ('status'|'allow'|'deny'|'delete'|'enable'|'disable'), "
        "rule (str opt, e.g. '22', '80/tcp', 'from 192.168.1.0/24')."
    )
    platforms   = ["linux"]

    SAFE_ACTIONS = {"status", "allow", "deny", "delete", "enable", "disable"}

    async def execute(self, action: str = "status", rule: str = "", **kwargs):
        if action not in self.SAFE_ACTIONS:
            return SkillResult(success=False, output="", error=f"Action must be one of: {self.SAFE_ACTIONS}")

        if action == "status":
            rc, out = await _run("sudo ufw status verbose")
        elif action in ("allow", "deny"):
            if not rule:
                return SkillResult(success=False, output="", error=f"rule required for {action}")
            rc, out = await _run(f"sudo ufw {action} {rule}")
        elif action == "delete":
            if not rule:
                return SkillResult(success=False, output="", error="rule required for delete")
            rc, out = await _run(f"sudo ufw delete {rule}")
        elif action == "enable":
            rc, out = await _run("echo y | sudo ufw enable")
        elif action == "disable":
            rc, out = await _run("sudo ufw disable")

        icons = {"status": "🔥", "allow": "✅", "deny": "🚫", "delete": "🗑️", "enable": "🔛", "disable": "🔴"}
        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"{icons.get(action,'🔥')} **UFW {action}**\n```\n{out[:1500]}\n```",
            data={"returncode": rc},
            error="" if ok else out[-200:],
        )
