"""
macos/applescript.py — Nexara Skills Warehouse
Run AppleScript and control macOS apps/notifications.

Dependencies: none
Platforms   : macos
"""

import asyncio

from skills.base import BaseSkill, SkillResult

TIMEOUT = 30


async def _run(cmd: str, timeout: int = TIMEOUT) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Timed out after {timeout}s"


class AppleScriptSkill(BaseSkill):
    name        = "applescript"
    description = "Run an AppleScript command on macOS. Args: script (str)."
    platforms   = ["macos"]

    # Block anything that touches system security dialogs or destructive ops
    _BLOCKED = ["do shell script", "system events", "keystroke", "delay 0"]

    async def execute(self, script: str = "", **kwargs) -> SkillResult:
        if not script:
            return SkillResult(success=False, output="", error="No script provided.")
        for pattern in self._BLOCKED:
            if pattern.lower() in script.lower():
                return SkillResult(success=False, output="", error=f"Blocked pattern: `{pattern}`")
        rc, out = await _run(f"osascript -e '{script}'")
        if rc == 0:
            return SkillResult(success=True, output=out or "✅ AppleScript executed.", data={})
        return SkillResult(success=False, output="", error=out)


class MacNotificationSkill(BaseSkill):
    name        = "mac_notification"
    description = "Send a macOS desktop notification. Args: title (str), message (str), subtitle (str opt)."
    platforms   = ["macos"]

    async def execute(
        self,
        title:    str = "Nexara",
        message:  str = "",
        subtitle: str = "",
        **kwargs,
    ) -> SkillResult:
        if not message:
            return SkillResult(success=False, output="", error="No message provided.")
        sub_part = f'subtitle "{subtitle}"' if subtitle else ""
        script   = (
            f'display notification "{message}" with title "{title}" {sub_part}'
        )
        rc, out = await _run(f"osascript -e '{script}'")
        if rc == 0:
            return SkillResult(success=True, output=f"🔔 Notification sent: **{title}**", data={})
        return SkillResult(success=False, output="", error=out)


class MacVolumeSkill(BaseSkill):
    name        = "mac_volume"
    description = "Get or set macOS system volume. Args: level (0-100, -1 to query)."
    platforms   = ["macos"]

    async def execute(self, level: int = -1, **kwargs) -> SkillResult:
        if level < 0:
            rc, out = await _run("osascript -e 'output volume of (get volume settings)'")
            if rc == 0:
                return SkillResult(success=True, output=f"🔊 Current volume: {out}%", data={"volume": out})
            return SkillResult(success=False, output="", error=out)
        level   = max(0, min(100, level))
        rc, out = await _run(f"osascript -e 'set volume output volume {level}'")
        if rc == 0:
            return SkillResult(success=True, output=f"🔊 Volume set to {level}%.", data={})
        return SkillResult(success=False, output="", error=out)


class SpotlightSearchSkill(BaseSkill):
    name        = "spotlight_search"
    description = "Search files on macOS using Spotlight (mdfind). Args: query (str), limit (int)."
    platforms   = ["macos"]

    async def execute(self, query: str = "", limit: int = 20, **kwargs) -> SkillResult:
        if not query:
            return SkillResult(success=False, output="", error="No query provided.")
        rc, out = await _run(f"mdfind '{query}' | head -{limit}")
        if rc == 0:
            lines   = out.splitlines()
            results = "\n".join(f"• `{l}`" for l in lines)
            return SkillResult(
                success=True,
                output=f"🔍 **Spotlight: `{query}`** ({len(lines)} results)\n\n{results}",
                data={"paths": lines},
            )
        return SkillResult(success=False, output="", error=out)
