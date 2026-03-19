"""
windows/windows_info.py — Nexara Skills Warehouse
Windows system information: OS version, hardware, memory.

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

class WindowsInfoSkill(BaseSkill):
    name        = "windows_info"
    description = "Get Windows system information: OS, CPU, RAM, disk."
    platforms   = ["windows"]

    async def execute(self, **kwargs):
        ps = (
            "Get-ComputerInfo | Select-Object "
            "WindowsProductName, WindowsVersion, OsTotalVisibleMemorySize, "
            "CsNumberOfProcessors, CsProcessors | Format-List"
        )
        rc1, os_out = await _run(f"powershell -NoProfile -Command "{ps}"")
        rc2, mem_out = await _run(
            "powershell -NoProfile -Command ""
            "Get-CimInstance Win32_OperatingSystem | "
            "Select-Object FreePhysicalMemory, TotalVisibleMemorySize | Format-List""
        )
        rc3, disk_out = await _run(
            "powershell -NoProfile -Command ""
            "Get-PSDrive -PSProvider FileSystem | "
            "Select-Object Name, Used, Free | Format-Table""
        )
        output = "🪟 **Windows System Info**\n"
        if rc1 == 0: output += f"```\n{os_out[:800]}\n```\n"
        if rc2 == 0: output += f"**Memory:**\n```\n{mem_out[:300]}\n```\n"
        if rc3 == 0: output += f"**Disks:**\n```\n{disk_out[:400]}\n```"
        return SkillResult(success=True, output=output, data={})
