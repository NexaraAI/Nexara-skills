"""
android/alarm_set.py — Nexara Skills Warehouse
Set a device alarm via Android's alarm clock intent.

Dependencies: none (uses am start)
Platforms   : android
"""

import asyncio
import re
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

class AlarmSetSkill(BaseSkill):
    name        = "alarm_set"
    description = "Set an Android alarm. Args: hour (int 0-23), minute (int 0-59), message (str opt), vibrate (bool, default True)."
    platforms   = ["android"]

    async def execute(self, hour: int = 8, minute: int = 0, message: str = "Nexara Alarm", vibrate: bool = True, **kwargs):
        hour   = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        vib    = "true" if vibrate else "false"
        cmd    = (
            f"am start -a android.intent.action.SET_ALARM "
            f"--ei android.intent.extra.alarm.HOUR {hour} "
            f"--ei android.intent.extra.alarm.MINUTES {minute} "
            f"--ez android.intent.extra.alarm.VIBRATE {vib} "
            f"--es android.intent.extra.alarm.MESSAGE '{message}' "
            f"--ez android.intent.extra.alarm.SKIP_UI true"
        )
        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"⏰ Alarm set for **{hour:02d}:{minute:02d}** — _{message}_",
                data={"hour": hour, "minute": minute, "message": message},
            )
        return SkillResult(success=False, output="", error=out)
