"""
android/media_control.py — Nexara Skills Warehouse
Android media player control, device sensors, WiFi management, screen brightness.

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


class MediaPlayerSkill(BaseSkill):
    name        = "media_player"
    description = "Control Android media playback. Args: action ('play'|'pause'|'next'|'previous'|'stop'|'info'), file_path (str opt)."
    platforms   = ["android"]

    ACTION_MAP = {
        "play":     "termux-media-player play",
        "pause":    "termux-media-player pause",
        "next":     "termux-media-player next",
        "previous": "termux-media-player prev",
        "stop":     "termux-media-player stop",
        "info":     "termux-media-player info",
    }

    async def execute(self, action: str = "info", file_path: str = "", **kwargs) -> SkillResult:
        if action == "play" and file_path:
            rc, out = await _run(f"termux-media-player play '{file_path}'")
        elif action in self.ACTION_MAP:
            rc, out = await _run(self.ACTION_MAP[action])
        else:
            return SkillResult(success=False, output="", error=f"Unknown action. Use: {list(self.ACTION_MAP)}")
        if rc == 0:
            icon = {"play":"▶️","pause":"⏸️","next":"⏭️","previous":"⏮️","stop":"⏹️","info":"ℹ️"}.get(action,"🎵")
            return SkillResult(success=True, output=f"{icon} Media {action}\n{out}", data={})
        return SkillResult(success=False, output="", error=out)


class SensorReadSkill(BaseSkill):
    name        = "sensor_read"
    description = "Read Android device sensors. Args: sensor_type ('accelerometer'|'gyroscope'|'light'|'magnetic'|'all')."
    platforms   = ["android"]

    async def execute(self, sensor_type: str = "all", **kwargs) -> SkillResult:
        rc, out = await _run(f"termux-sensor -s {sensor_type} -n 1", timeout=10)
        if rc == 0:
            try:
                data  = json.loads(out)
                lines = [f"📡 **Sensor: {sensor_type}**\n"]
                for sensor, values in data.items():
                    lines.append(f"**{sensor}:**")
                    if isinstance(values, dict):
                        for k, v in values.items():
                            lines.append(f"  {k}: {v}")
                    else:
                        lines.append(f"  {values}")
                return SkillResult(success=True, output="\n".join(lines), data=data)
            except json.JSONDecodeError:
                return SkillResult(success=True, output=f"📡 Sensor Data\n{out}", data={})
        return SkillResult(success=False, output="", error=out)


class WiFiControlSkill(BaseSkill):
    name        = "wifi_control"
    description = "Enable, disable, or scan WiFi networks. Args: action ('enable'|'disable'|'scan'|'info')."
    platforms   = ["android"]

    async def execute(self, action: str = "info", **kwargs) -> SkillResult:
        if action == "enable":
            rc, out = await _run("termux-wifi-enable true")
        elif action == "disable":
            rc, out = await _run("termux-wifi-enable false")
        elif action == "scan":
            rc, out = await _run("termux-wifi-scaninfo")
            if rc == 0:
                try:
                    networks = json.loads(out)
                    lines    = [f"📶 **WiFi Scan** ({len(networks)} networks)\n"]
                    for n in sorted(networks, key=lambda x: x.get("rssi", -999), reverse=True)[:15]:
                        ssid = n.get("ssid", "Hidden")
                        rssi = n.get("rssi", "?")
                        freq = n.get("frequency", "?")
                        lines.append(f"  📶 **{ssid}**  signal: {rssi} dBm  freq: {freq} MHz")
                    return SkillResult(success=True, output="\n".join(lines), data={"networks": networks})
                except json.JSONDecodeError:
                    return SkillResult(success=True, output=out, data={})
        else:
            rc, out = await _run("termux-wifi-connectioninfo")
            if rc == 0:
                try:
                    info = json.loads(out)
                    return SkillResult(
                        success=True,
                        output=(
                            f"📶 **WiFi Info**\n"
                            f"  SSID   : {info.get('ssid','?')}\n"
                            f"  IP     : {info.get('ip','?')}\n"
                            f"  Signal : {info.get('rssi','?')} dBm\n"
                            f"  Speed  : {info.get('link_speed','?')} Mbps"
                        ),
                        data=info,
                    )
                except json.JSONDecodeError:
                    return SkillResult(success=True, output=out, data={})
        if rc == 0:
            return SkillResult(success=True, output=f"📶 WiFi {action} successful.", data={})
        return SkillResult(success=False, output="", error=out)


class ScreenBrightnessSkill(BaseSkill):
    name        = "screen_brightness"
    description = "Set Android screen brightness. Args: level (int 0-255)."
    platforms   = ["android"]

    async def execute(self, level: int = 128, **kwargs) -> SkillResult:
        level   = max(0, min(255, level))
        rc, out = await _run(f"termux-brightness {level}")
        if rc == 0:
            pct = round(level / 255 * 100)
            return SkillResult(success=True, output=f"☀️ Brightness set to {level}/255 ({pct}%)", data={})
        return SkillResult(success=False, output="", error=out)
