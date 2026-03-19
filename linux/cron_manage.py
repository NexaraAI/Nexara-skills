"""
linux/cron_manage.py — Nexara Skills Warehouse
List, add, and remove cron jobs.

Dependencies: none (uses crontab CLI)
Platforms   : linux
"""

import asyncio
import tempfile
from pathlib import Path
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=15, input_data=None):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        stdin=asyncio.subprocess.PIPE if input_data else None)
    try:
        inp = input_data.encode() if input_data else None
        out, _ = await asyncio.wait_for(proc.communicate(input=inp), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class CronManageSkill(BaseSkill):
    name        = "cron_manage"
    description = (
        "Manage cron jobs. "
        "Args: action ('list'|'add'|'remove'), "
        "schedule (str, cron format e.g. '0 8 * * *'), command (str), "
        "comment (str opt)."
    )
    platforms   = ["linux"]

    async def execute(self, action: str = "list", schedule: str = "", command: str = "", comment: str = "", **kwargs):
        if action == "list":
            rc, out = await _run("crontab -l 2>/dev/null || echo '(no crontab)'")
            return SkillResult(success=True, output=f"⏰ **Crontab**\n```\n{out}\n```", data={})

        if action == "add":
            if not schedule or not command:
                return SkillResult(success=False, output="", error="schedule and command are required.")
            rc, existing = await _run("crontab -l 2>/dev/null")
            lines = [l for l in existing.splitlines() if l.strip()] if rc == 0 else []
            entry = f"{'# ' + comment + chr(10) if comment else ''}{schedule} {command}"
            lines.append(entry)
            new_cron = "\n".join(lines) + "\n"
            rc2, out2 = await _run("crontab -", input_data=new_cron)
            if rc2 == 0:
                return SkillResult(success=True, output=f"✅ Cron job added:\n`{schedule} {command}`", data={})
            return SkillResult(success=False, output="", error=out2)

        if action == "remove":
            if not command:
                return SkillResult(success=False, output="", error="command pattern required to remove.")
            rc, existing = await _run("crontab -l 2>/dev/null")
            if rc != 0:
                return SkillResult(success=False, output="", error="No crontab found.")
            lines     = existing.splitlines()
            new_lines = [l for l in lines if command not in l]
            removed   = len(lines) - len(new_lines)
            if removed == 0:
                return SkillResult(success=True, output=f"No cron jobs containing `{command}` found.", data={})
            new_cron = "\n".join(new_lines) + "\n"
            rc2, out2 = await _run("crontab -", input_data=new_cron)
            if rc2 == 0:
                return SkillResult(success=True, output=f"🗑️ Removed {removed} cron job(s) containing `{command}`", data={})
            return SkillResult(success=False, output="", error=out2)

        return SkillResult(success=False, output="", error=f"Unknown action: {action}")
