"""
android/device_control.py — Nexara Skills Warehouse
Android device controls: torch, volume, vibrate, GPS, notifications, app launcher.

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


class TorchSkill(BaseSkill):
    name        = "torch"
    description = "Toggle device flashlight. Args: state ('on'|'off')."
    platforms   = ["android"]

    async def execute(self, state: str = "on", **kwargs) -> SkillResult:
        enabled = "true" if state.lower() in ("on", "1", "true") else "false"
        rc, out = await _run(f"termux-torch {enabled}")
        emoji   = "🔦" if enabled == "true" else "⬛"
        if rc == 0:
            return SkillResult(success=True, output=f"{emoji} Torch **{state}**.", data={})
        return SkillResult(success=False, output="", error=out)


class VolumeSkill(BaseSkill):
    name        = "volume"
    description = "Get or set volume. Args: stream ('music'|'ring'|'alarm'|...), level (0-15, -1=query)."
    platforms   = ["android"]

    async def execute(self, stream: str = "music", level: int = -1, **kwargs) -> SkillResult:
        if level < 0:
            rc, out = await _run("termux-volume")
        else:
            rc, out = await _run(f"termux-volume {stream} {level}")
        if rc == 0:
            return SkillResult(success=True, output=f"🔊 Volume:\n{out}", data={})
        return SkillResult(success=False, output="", error=out)


class VibrateSkill(BaseSkill):
    name        = "vibrate"
    description = "Vibrate device. Args: duration_ms (default 500)."
    platforms   = ["android"]

    async def execute(self, duration_ms: int = 500, **kwargs) -> SkillResult:
        rc, out = await _run(f"termux-vibrate -d {duration_ms}")
        if rc == 0:
            return SkillResult(success=True, output=f"📳 Vibrated {duration_ms}ms.", data={})
        return SkillResult(success=False, output="", error=out)


class LocationSkill(BaseSkill):
    name        = "location"
    description = "Get GPS coordinates. Args: provider ('gps'|'network'|'passive')."
    platforms   = ["android"]

    async def execute(self, provider: str = "gps", **kwargs) -> SkillResult:
        rc, out = await _run(f"termux-location -p {provider} -r once", timeout=30)
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        try:
            loc = json.loads(out)
            lat = loc.get("latitude",  "?")
            lng = loc.get("longitude", "?")
            alt = loc.get("altitude",  "?")
            acc = loc.get("accuracy",  "?")
            return SkillResult(
                success=True,
                output=(
                    f"📍 **Location**\n"
                    f"  Lat/Lng  : {lat}, {lng}\n"
                    f"  Altitude : {alt}m\n"
                    f"  Accuracy : ±{acc}m\n"
                    f"  Maps     : https://maps.google.com/?q={lat},{lng}"
                ),
                data=loc,
            )
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out, data={})


class NotificationReaderSkill(BaseSkill):
    name        = "notification_reader"
    description = "Read current Android notifications."
    platforms   = ["android"]

    async def execute(self, **kwargs) -> SkillResult:
        rc, out = await _run("termux-notification-list")
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        try:
            notifications = json.loads(out)
            if not notifications:
                return SkillResult(success=True, output="🔔 No notifications.", data={})
            lines = [f"🔔 **{len(notifications)} Notification(s)**\n"]
            for n in notifications[:10]:
                app   = n.get("packageName", "?")
                title = n.get("title", "(no title)")
                text  = n.get("content", "")
                lines.append(f"• **{title}** [{app}]")
                if text:
                    lines.append(f"  {text[:120]}")
            return SkillResult(
                success=True, output="\n".join(lines),
                data={"notifications": notifications},
            )
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out[:1000], data={})


class AppLauncherSkill(BaseSkill):
    name        = "app_launcher"
    description = "Launch an Android app by name or package. Args: app (str)."
    platforms   = ["android"]

    ALIASES: dict[str, str] = {
        "chrome":   "com.android.chrome/com.google.android.apps.chrome.Main",
        "spotify":  "com.spotify.music/com.spotify.music.MainActivity",
        "youtube":  "com.google.android.youtube/com.google.android.youtube.HomeActivity",
        "maps":     "com.google.android.apps.maps/com.google.android.maps.MapsActivity",
        "camera":   "com.android.camera2/com.android.camera.CameraActivity",
        "settings": "com.android.settings/.Settings",
        "telegram": "org.telegram.messenger/.DefaultIcon",
        "whatsapp": "com.whatsapp/.HomeActivity",
        "termux":   "com.termux/.HomeActivity",
    }

    async def execute(self, app: str = "", **kwargs) -> SkillResult:
        if not app:
            return SkillResult(success=False, output="", error="No app specified.")
        target = self.ALIASES.get(app.lower(), app)
        cmd    = (
            f"am start -n {target}"
            if "/" in target
            else f"am start $(pm resolve-activity --brief {target} | tail -n 1)"
        )
        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(success=True, output=f"🚀 Launched `{app}`.", data={"target": target})
        return SkillResult(success=False, output="", error=out)
