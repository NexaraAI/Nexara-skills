"""
macos/brew.py — Nexara Skills Warehouse
Homebrew package management for macOS.

Dependencies: none (uses brew CLI)
Platforms   : macos
"""

import asyncio

from skills.base import BaseSkill, SkillResult

TIMEOUT = 120


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


class BrewInstallSkill(BaseSkill):
    name        = "brew_install"
    description = "Install a Homebrew package. Args: package (str), cask (bool, for GUI apps)."
    platforms   = ["macos"]

    async def execute(self, package: str = "", cask: bool = False, **kwargs) -> SkillResult:
        if not package:
            return SkillResult(success=False, output="", error="No package specified.")
        flag    = "--cask" if cask else ""
        rc, out = await _run(f"brew install {flag} {package}")
        if rc == 0:
            return SkillResult(success=True, output=f"✅ Installed `{package}`.", data={})
        return SkillResult(success=False, output="", error=out[-500:])


class BrewUninstallSkill(BaseSkill):
    name        = "brew_uninstall"
    description = "Uninstall a Homebrew package. Args: package (str)."
    platforms   = ["macos"]

    async def execute(self, package: str = "", **kwargs) -> SkillResult:
        if not package:
            return SkillResult(success=False, output="", error="No package specified.")
        rc, out = await _run(f"brew uninstall {package}")
        if rc == 0:
            return SkillResult(success=True, output=f"🗑️ Uninstalled `{package}`.", data={})
        return SkillResult(success=False, output="", error=out[-300:])


class BrewSearchSkill(BaseSkill):
    name        = "brew_search"
    description = "Search for Homebrew packages. Args: query (str)."
    platforms   = ["macos"]

    async def execute(self, query: str = "", **kwargs) -> SkillResult:
        if not query:
            return SkillResult(success=False, output="", error="No query provided.")
        rc, out = await _run(f"brew search {query}")
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"🍺 **Brew Search: `{query}`**\n```\n{out[:1500]}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)


class BrewUpdateSkill(BaseSkill):
    name        = "brew_update"
    description = "Update Homebrew and optionally upgrade all packages. Args: upgrade (bool)."
    platforms   = ["macos"]

    async def execute(self, upgrade: bool = False, **kwargs) -> SkillResult:
        rc, out = await _run("brew update")
        if rc != 0:
            return SkillResult(success=False, output="", error=out[-300:])
        if upgrade:
            rc2, out2 = await _run("brew upgrade", timeout=300)
            if rc2 != 0:
                return SkillResult(success=False, output="", error=out2[-300:])
            return SkillResult(success=True, output="✅ Updated Homebrew and upgraded all packages.", data={})
        return SkillResult(success=True, output="✅ Homebrew updated.", data={})
