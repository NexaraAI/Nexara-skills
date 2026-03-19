"""
android/tts_speak.py — Nexara Skills Warehouse
Text-to-speech on Android via termux-tts-speak.

Dependencies: none
Platforms   : android
"""

import asyncio
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=30):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class TtsSpeakSkill(BaseSkill):
    name        = "tts_speak"
    description = "Speak text aloud on the Android device. Args: text (str), rate (float 0.5-2.0), pitch (float 0.5-2.0)."
    platforms   = ["android"]

    async def execute(self, text: str = "", rate: float = 1.0, pitch: float = 1.0, **kwargs):
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        text  = text[:500].replace("'", " ")
        rate  = max(0.5, min(2.0, rate))
        pitch = max(0.5, min(2.0, pitch))
        rc, out = await _run(f"termux-tts-speak -r {rate} -p {pitch} '{text}'")
        if rc == 0:
            return SkillResult(success=True, output=f"🔊 Speaking: _{text[:60]}_", data={})
        return SkillResult(success=False, output="", error=out)
