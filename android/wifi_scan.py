"""
android/wifi_scan.py — Nexara Skills Warehouse
Scan nearby WiFi networks via Termux:API.

Dependencies: none
Platforms   : android
"""

import asyncio
import json
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=20):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class WifiScanSkill(BaseSkill):
    name        = "wifi_scan"
    description = "Scan for nearby WiFi networks. Returns SSIDs, signal strength, and security."
    platforms   = ["android"]

    async def execute(self, **kwargs):
        rc, out = await _run("termux-wifi-scaninfo")
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        try:
            networks = json.loads(out)
            if not networks:
                return SkillResult(success=True, output="📶 No networks found.", data={})
            networks = sorted(networks, key=lambda n: n.get("level", -100), reverse=True)
            lines    = [f"📶 **{len(networks)} WiFi Networks**\n"]
            for n in networks[:15]:
                ssid   = n.get("SSID", "Hidden")
                level  = n.get("level", "?")
                secure = n.get("capabilities", "")
                freq   = n.get("frequency", "?")
                bars   = "▓" * max(0, min(4, (level + 100) // 20)) + "░" * (4 - max(0, min(4, (level + 100) // 20)))
                sec    = "🔒" if "WPA" in secure or "WEP" in secure else "🔓"
                lines.append(f"  {sec} **{ssid}**  {bars}  {level} dBm  {freq} MHz")
            return SkillResult(success=True, output="\n".join(lines), data={"networks": networks})
        except json.JSONDecodeError:
            return SkillResult(success=True, output=out[:1000], data={})
