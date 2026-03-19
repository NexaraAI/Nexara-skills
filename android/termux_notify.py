"""
android/termux_notify.py — Nexara Skills Warehouse
Rich Termux notifications with action buttons, ongoing alerts, and TTS.

Dependencies: none
Platforms   : android
"""

import asyncio

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 15) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Command timed out"


class TermuxNotifySkill(BaseSkill):
    name        = "termux_notify"
    description = (
        "Send a rich Android notification via Termux. "
        "Args: title (str), content (str), id (int opt), "
        "priority ('high'|'low'|'default'), ongoing (bool), sound (bool)."
    )
    platforms   = ["android"]

    async def execute(
        self,
        title:    str  = "Nexara",
        content:  str  = "",
        id:       int  = 1,
        priority: str  = "default",
        ongoing:  bool = False,
        sound:    bool = False,
        **kwargs,
    ) -> SkillResult:
        if not content:
            return SkillResult(success=False, output="", error="No content provided.")

        cmd = (
            f'termux-notification '
            f'--title "{title}" '
            f'--content "{content}" '
            f'--id {id} '
            f'--priority {priority}'
        )
        if ongoing: cmd += " --ongoing"
        if sound:   cmd += " --sound"

        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"🔔 Notification sent: **{title}**\n_{content}_",
                data={"id": id},
            )
        return SkillResult(success=False, output="", error=out)


class TermuxTTSSkill(BaseSkill):
    name        = "tts_speak"
    description = "Speak text aloud using Android Text-to-Speech. Args: text (str), language (str opt, e.g. 'en'), rate (float 0.5-2.0)."
    platforms   = ["android"]

    async def execute(
        self,
        text:     str   = "",
        language: str   = "en",
        rate:     float = 1.0,
        **kwargs,
    ) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        rate    = max(0.5, min(2.0, rate))
        cmd     = f'termux-tts-speak -l {language} -r {rate} "{text}"'
        rc, out = await _run(cmd, timeout=30)
        if rc == 0:
            preview = text[:60] + ("…" if len(text) > 60 else "")
            return SkillResult(success=True, output=f"🔊 Speaking: _{preview}_", data={})
        return SkillResult(success=False, output="", error=out)


class TermuxToastSkill(BaseSkill):
    name        = "toast"
    description = "Show a brief Android toast notification. Args: text (str), short (bool, default True)."
    platforms   = ["android"]

    async def execute(self, text: str = "", short: bool = True, **kwargs) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        flag    = "-s" if short else "-l"
        rc, out = await _run(f'termux-toast {flag} "{text}"')
        if rc == 0:
            return SkillResult(success=True, output=f"💬 Toast: _{text[:60]}_", data={})
        return SkillResult(success=False, output="", error=out)
