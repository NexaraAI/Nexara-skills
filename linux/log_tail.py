"""
linux/log_tail.py — Nexara Skills Warehouse
Tail and search log files.

Dependencies: none
Platforms   : linux
"""

import asyncio
from pathlib import Path
from skills.base import BaseSkill, SkillResult

COMMON_LOGS = {
    "syslog":  "/var/log/syslog",
    "auth":    "/var/log/auth.log",
    "nginx":   "/var/log/nginx/access.log",
    "nginx_error": "/var/log/nginx/error.log",
    "apache":  "/var/log/apache2/access.log",
    "nexara":  "~/.nexara/nexara.log",
    "install": "~/.nexara/install.log",
}

async def _run(cmd, timeout=15):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class LogTailSkill(BaseSkill):
    name        = "log_tail"
    description = (
        "Tail or search a log file. "
        "Args: log (str — path or alias like 'syslog'|'nginx'|'nexara'), "
        "lines (int, default 50), grep (str opt — filter pattern)."
    )
    platforms   = ["linux"]

    async def execute(self, log: str = "nexara", lines: int = 50, grep: str = "", **kwargs):
        if not log:
            aliases = ", ".join(f"`{k}`" for k in COMMON_LOGS)
            return SkillResult(success=False, output=f"Available log aliases: {aliases}", error="No log specified.")
        path = COMMON_LOGS.get(log.lower(), log)
        path = str(Path(path).expanduser())
        lines = max(1, min(500, lines))

        if grep:
            cmd = f"grep -i '{grep}' '{path}' | tail -{lines}"
        else:
            cmd = f"tail -{lines} '{path}'"

        rc, out = await _run(f"sudo {cmd} 2>/dev/null || {cmd}")
        if not out:
            return SkillResult(success=True, output=f"📋 `{path}` is empty or not found.", data={})
        return SkillResult(
            success=True,
            output=f"📋 **`{path}`**{(' | grep: '+grep) if grep else ''}\n```\n{out[:3000]}\n```",
            data={"path": path, "lines": len(out.splitlines())},
        )
