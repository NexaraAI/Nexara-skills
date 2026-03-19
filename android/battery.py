"""
android/battery.py — Nexara Skills Warehouse
Battery level, status, and health via Termux:API.

Dependencies: none (uses termux-battery-status CLI)
Platforms   : android
"""

import asyncio
import json

from skills.base import BaseSkill, SkillResult

_GUARD_MSG = (
    "⚠️ Termux:API required.\n"
    "Install from F-Droid, then run `pkg install termux-api`."
)


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


class BatterySkill(BaseSkill):
    name        = "battery"
    description = "Get Android battery percentage, status, and health."
    platforms   = ["android"]

    async def execute(self, **kwargs) -> SkillResult:
        rc, out = await _run("termux-battery-status")
        if rc != 0:
            return SkillResult(success=False, output=_GUARD_MSG, error=out)
        try:
            data    = json.loads(out)
            pct     = data.get("percentage", "?")
            status  = data.get("status",     "?")
            health  = data.get("health",     "?")
            plugged = data.get("plugged",    "?")
            return SkillResult(
                success=True,
                output=(
                    f"🔋 **Battery**\n"
                    f"  Level   : {pct}%\n"
                    f"  Status  : {status}\n"
                    f"  Health  : {health}\n"
                    f"  Plugged : {plugged}"
                ),
                data=data,
            )
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out, data={})


class DeviceStatsSkill(BaseSkill):
    name        = "device_stats"
    description = "Full Android device snapshot: battery, Wi-Fi, storage, uptime."
    platforms   = ["android"]

    async def execute(self, **kwargs) -> SkillResult:
        _, battery_raw = await _run("termux-battery-status")
        _, wifi_raw    = await _run("termux-wifi-connectioninfo")
        _, storage_raw = await _run("df -h /data/data/com.termux/files")
        _, uptime_raw  = await _run("uptime -p")

        lines = ["📊 **Device Stats**\n"]
        try:
            b = json.loads(battery_raw)
            lines.append(f"🔋 Battery : {b.get('percentage')}%  ({b.get('status')})")
        except Exception:
            lines.append(f"🔋 Battery : {battery_raw[:60]}")
        try:
            w    = json.loads(wifi_raw)
            ssid = w.get("ssid") or w.get("bssid") or "Unknown"
            ip   = w.get("ip", "N/A")
            lines.append(f"📶 Wi-Fi   : {ssid}  ({ip})")
        except Exception:
            lines.append(f"📶 Wi-Fi   : {wifi_raw[:60]}")
        for line in storage_raw.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                lines.append(f"💾 Storage : {parts[3]} free / {parts[1]} total")
                break
        lines.append(f"⏱️  Uptime  : {uptime_raw}")
        return SkillResult(success=True, output="\n".join(lines), data={})
