"""
windows/windows_notify.py — Nexara Skills Warehouse
Windows 10/11 toast notifications via PowerShell.

Dependencies: none
Platforms   : windows
"""

import asyncio
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

class WindowsNotifySkill(BaseSkill):
    name        = "windows_notify"
    description = "Send a Windows toast notification. Args: title (str), message (str), duration ('short'|'long')."
    platforms   = ["windows"]

    async def execute(self, title: str = "Nexara", message: str = "", duration: str = "short", **kwargs):
        if not message:
            return SkillResult(success=False, output="", error="No message provided.")
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipIcon = "Info"
$notify.BalloonTipTitle = "{title}"
$notify.BalloonTipText = "{message}"
$notify.Visible = $true
$notify.ShowBalloonTip({"5000" if duration == "short" else "10000"})
Start-Sleep -Seconds 2
$notify.Dispose()
"""
        cmd = f"powershell -NoProfile -NonInteractive -Command "{ps_script.strip()}""
        rc, out = await _run(cmd)
        if rc == 0:
            return SkillResult(success=True, output=f"🔔 Notification sent: **{title}**\n_{message}_", data={})
        return SkillResult(success=False, output="", error=out)
