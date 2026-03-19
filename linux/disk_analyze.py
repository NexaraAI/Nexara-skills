"""
linux/disk_analyze.py — Nexara Skills Warehouse
Detailed disk usage analysis — find large files and directories.

Dependencies: none (uses du, find)
Platforms   : linux
"""

import asyncio
from pathlib import Path
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

class DiskAnalyzeSkill(BaseSkill):
    name        = "disk_analyze"
    description = (
        "Analyze disk usage of a directory. Find largest files and subdirectories. "
        "Args: path (str, default '~'), depth (int 1-3, default 1), "
        "min_size (str opt, e.g. '100M'), find_large (bool, default True)."
    )
    platforms   = ["linux"]

    async def execute(self, path: str = "~", depth: int = 1, find_large: bool = True, min_size: str = "50M", **kwargs):
        p     = Path(path).expanduser()
        depth = max(1, min(3, depth))

        rc1, du_out = await _run(f"du -h --max-depth={depth} '{p}' 2>/dev/null | sort -rh | head -20")
        lines = [f"💾 **Disk Usage: `{p}`**\n```\n{du_out[:1500]}\n```"]

        if find_large:
            rc2, lg_out = await _run(f"find '{p}' -type f -size +{min_size} -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -10")
            if lg_out:
                file_lines = []
                for line in lg_out.splitlines()[:10]:
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        size = int(parts[0])
                        human = f"{size/1_073_741_824:.1f}GB" if size > 1_073_741_824 else f"{size/1_048_576:.1f}MB"
                        file_lines.append(f"  • `{parts[1]}` ({human})")
                if file_lines:
                    lines.append(f"\n🔍 **Large files (>{min_size}):**\n" + "\n".join(file_lines))

        return SkillResult(success=True, output="\n".join(lines), data={})
