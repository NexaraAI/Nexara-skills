"""
android/sms.py — Nexara Skills Warehouse
Read/send SMS and search contacts via Termux:API.

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
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, out.decode("utf-8", errors="replace").strip()


class ReadSMSSkill(BaseSkill):
    name        = "read_sms"
    description = "Read SMS messages. Args: limit (default 10), inbox_type ('inbox'|'sent'|'all')."
    platforms   = ["android"]

    async def execute(self, limit: int = 10, inbox_type: str = "inbox", **kwargs) -> SkillResult:
        rc, out = await _run(f"termux-sms-list -l {limit} -t {inbox_type}")
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        try:
            msgs  = json.loads(out)
            if not msgs:
                return SkillResult(success=True, output="📭 No messages.", data={})
            lines = [f"💬 **{len(msgs)} SMS ({inbox_type})**\n"]
            for m in msgs[:limit]:
                lines.append(
                    f"• **{m.get('address','?')}** — {m.get('date','')}\n"
                    f"  {m.get('body','')[:200]}"
                )
            return SkillResult(success=True, output="\n".join(lines), data={"messages": msgs})
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out[:2000], data={})


class SendSMSSkill(BaseSkill):
    name        = "send_sms"
    description = "Send an SMS. Args: number (str), message (str)."
    platforms   = ["android"]

    async def execute(self, number: str = "", message: str = "", **kwargs) -> SkillResult:
        if not number or not message:
            return SkillResult(success=False, output="", error="number and message are required.")
        number  = number.replace('"', "").replace("'", "")
        message = message.replace('"', '\\"')
        rc, out = await _run(f'termux-sms-send -n "{number}" "{message}"')
        if rc == 0:
            return SkillResult(success=True, output=f"✉️ SMS sent to {number}.", data={})
        return SkillResult(success=False, output="", error=out)


class ReadContactsSkill(BaseSkill):
    name        = "read_contacts"
    description = "Search device contacts by name. Args: query (str)."
    platforms   = ["android"]

    async def execute(self, query: str = "", **kwargs) -> SkillResult:
        rc, out = await _run("termux-contact-list")
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        try:
            contacts = json.loads(out)
            if query:
                contacts = [c for c in contacts if query.lower() in c.get("name", "").lower()]
            if not contacts:
                return SkillResult(success=True, output="No contacts found.", data={})
            lines = [f"👤 **{len(contacts)} Contact(s)**\n"]
            for c in contacts[:20]:
                lines.append(f"• **{c.get('name','?')}** — {c.get('number','')}")
            return SkillResult(success=True, output="\n".join(lines), data={"contacts": contacts[:20]})
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out[:1000], data={})
