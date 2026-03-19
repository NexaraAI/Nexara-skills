"""
android/call_log.py — Nexara Skills Warehouse
Read call history and make phone calls via Termux:API.

Dependencies: none
Platforms   : android
"""

import asyncio
import json

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 20) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Command timed out"


class CallLogSkill(BaseSkill):
    name        = "call_log"
    description = "Read recent call history. Args: limit (int, default 10), type ('all'|'incoming'|'outgoing'|'missed')."
    platforms   = ["android"]

    async def execute(self, limit: int = 10, type: str = "all", **kwargs) -> SkillResult:
        rc, out = await _run(f"termux-call-log -l {limit} -t {type}")
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        try:
            calls = json.loads(out)
            if not calls:
                return SkillResult(success=True, output="📞 No call history found.", data={})
            type_icons = {"INCOMING": "📲", "OUTGOING": "📤", "MISSED": "❌", "REJECTED": "🚫"}
            lines = [f"📞 **Call Log** ({len(calls)} calls)\n"]
            for c in calls:
                number    = c.get("number", "?")
                name      = c.get("name", "")
                duration  = c.get("duration", 0)
                date      = c.get("date", "?")
                call_type = c.get("type", "?").upper()
                icon      = type_icons.get(call_type, "📞")
                contact   = f"{name} ({number})" if name else number
                mins, secs = divmod(int(duration), 60)
                dur_str   = f"{mins}m {secs}s" if mins else f"{secs}s"
                lines.append(f"{icon} **{contact}** — {dur_str}  _{date}_")
            return SkillResult(success=True, output="\n".join(lines), data={"calls": calls})
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out[:2000], data={})


class PhoneCallSkill(BaseSkill):
    name        = "phone_call"
    description = "Make a phone call. Args: number (str)."
    platforms   = ["android"]

    async def execute(self, number: str = "", **kwargs) -> SkillResult:
        if not number:
            return SkillResult(success=False, output="", error="No phone number provided.")
        number  = number.replace('"', "").replace("'", "").strip()
        rc, out = await _run(f'termux-telephony-call "{number}"')
        if rc == 0:
            return SkillResult(success=True, output=f"📞 Calling **{number}**...", data={"number": number})
        return SkillResult(success=False, output="", error=out)
