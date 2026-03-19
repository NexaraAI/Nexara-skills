"""
linux/apt_manage.py — Nexara Skills Warehouse
APT package management for Debian/Ubuntu-based Linux systems.

Dependencies: none (uses apt-get CLI)
Platforms   : linux
"""

import asyncio

from skills.base import BaseSkill, SkillResult

TIMEOUT = 120


async def _run(cmd: str, timeout: int = TIMEOUT) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={"DEBIAN_FRONTEND": "noninteractive", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Timed out after {timeout}s"


class AptInstallSkill(BaseSkill):
    name        = "apt_install"
    description = "Install a package via apt. Args: package (str)."
    platforms   = ["linux"]

    async def execute(self, package: str = "", **kwargs) -> SkillResult:
        if not package:
            return SkillResult(success=False, output="", error="No package specified.")
        rc, out = await _run(f"sudo apt-get install -y -q {package}")
        if rc == 0:
            return SkillResult(success=True, output=f"✅ Installed `{package}`.", data={})
        return SkillResult(success=False, output="", error=out[-500:])


class AptRemoveSkill(BaseSkill):
    name        = "apt_remove"
    description = "Remove a package via apt. Args: package (str)."
    platforms   = ["linux"]

    async def execute(self, package: str = "", **kwargs) -> SkillResult:
        if not package:
            return SkillResult(success=False, output="", error="No package specified.")
        rc, out = await _run(f"sudo apt-get remove -y -q {package}")
        if rc == 0:
            return SkillResult(success=True, output=f"🗑️ Removed `{package}`.", data={})
        return SkillResult(success=False, output="", error=out[-500:])


class AptSearchSkill(BaseSkill):
    name        = "apt_search"
    description = "Search for a package in apt repositories. Args: query (str)."
    platforms   = ["linux"]

    async def execute(self, query: str = "", **kwargs) -> SkillResult:
        if not query:
            return SkillResult(success=False, output="", error="No query provided.")
        rc, out = await _run(f"apt-cache search {query} | head -20")
        if rc == 0:
            return SkillResult(success=True, output=f"📦 **APT Search: `{query}`**\n```\n{out}\n```", data={})
        return SkillResult(success=False, output="", error=out)


class AptUpdateSkill(BaseSkill):
    name        = "apt_update"
    description = "Update apt package lists and optionally upgrade all packages. Args: upgrade (bool)."
    platforms   = ["linux"]

    async def execute(self, upgrade: bool = False, **kwargs) -> SkillResult:
        rc, out = await _run("sudo apt-get update -q")
        if rc != 0:
            return SkillResult(success=False, output="", error=out[-300:])
        if upgrade:
            rc2, out2 = await _run("sudo apt-get upgrade -y -q", timeout=300)
            if rc2 != 0:
                return SkillResult(success=False, output="", error=out2[-300:])
            return SkillResult(success=True, output="✅ Updated and upgraded all packages.", data={})
        return SkillResult(success=True, output="✅ Package lists updated.", data={})
