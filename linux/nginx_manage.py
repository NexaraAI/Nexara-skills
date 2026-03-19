"""
linux/nginx_manage.py — Nexara Skills Warehouse
Nginx web server management.

Dependencies: nginx
Platforms   : linux
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

class NginxManageSkill(BaseSkill):
    name        = "nginx_manage"
    description = "Manage Nginx. Args: action ('status'|'start'|'stop'|'restart'|'reload'|'test_config'|'sites')."
    platforms   = ["linux"]

    ACTIONS = {"status", "start", "stop", "restart", "reload", "test_config", "sites"}

    async def execute(self, action: str = "status", **kwargs):
        if action not in self.ACTIONS:
            return SkillResult(success=False, output="", error=f"Action must be one of: {self.ACTIONS}")

        if action == "status":
            rc, out = await _run("systemctl status nginx --no-pager -l 2>/dev/null || nginx -v 2>&1 && echo nginx not managed by systemd")
        elif action in ("start", "stop", "restart", "reload"):
            rc, out = await _run(f"sudo systemctl {action} nginx")
        elif action == "test_config":
            rc, out = await _run("sudo nginx -t")
        elif action == "sites":
            rc, out = await _run("ls -la /etc/nginx/sites-enabled/ 2>/dev/null || ls /etc/nginx/conf.d/ 2>/dev/null")

        icons = {"status": "ℹ️", "start": "▶️", "stop": "⏹", "restart": "🔄", "reload": "♻️", "test_config": "🔧", "sites": "🌐"}
        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"{icons.get(action,'🌐')} **Nginx {action}**\n```\n{out[:1500]}\n```",
            data={"returncode": rc},
            error="" if ok else out[-200:],
        )
