"""
linux/docker_ops.py — Nexara Skills Warehouse
Docker container and image management.

Dependencies: none (uses docker CLI)
Platforms   : linux
"""

import asyncio

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 60) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Timed out after {timeout}s"


class DockerListSkill(BaseSkill):
    name        = "docker_list"
    description = "List Docker containers and images. Args: what ('containers'|'images'|'all')."
    platforms   = ["linux"]

    async def execute(self, what: str = "containers", **kwargs) -> SkillResult:
        lines = []
        if what in ("containers", "all"):
            rc, out = await _run("docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'")
            if rc == 0: lines.append(f"**Containers:**\n```\n{out}\n```")
            else:       return SkillResult(success=False, output="", error=out)
        if what in ("images", "all"):
            rc, out = await _run("docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'")
            if rc == 0: lines.append(f"**Images:**\n```\n{out}\n```")
        return SkillResult(success=True, output="\n\n".join(lines) or "Nothing found.", data={})


class DockerRunSkill(BaseSkill):
    name        = "docker_run"
    description = "Start, stop, or restart a Docker container. Args: container (str), action ('start'|'stop'|'restart')."
    platforms   = ["linux"]

    ALLOWED = {"start", "stop", "restart"}

    async def execute(self, container: str = "", action: str = "start", **kwargs) -> SkillResult:
        if not container:
            return SkillResult(success=False, output="", error="No container specified.")
        if action not in self.ALLOWED:
            return SkillResult(success=False, output="", error=f"Action must be one of: {self.ALLOWED}")
        rc, out = await _run(f"docker {action} {container}")
        if rc == 0:
            return SkillResult(success=True, output=f"🐳 `{container}` {action}ed.", data={})
        return SkillResult(success=False, output="", error=out)


class DockerLogsSkill(BaseSkill):
    name        = "docker_logs"
    description = "View recent logs from a Docker container. Args: container (str), lines (int, default 50)."
    platforms   = ["linux"]

    async def execute(self, container: str = "", lines: int = 50, **kwargs) -> SkillResult:
        if not container:
            return SkillResult(success=False, output="", error="No container specified.")
        rc, out = await _run(f"docker logs --tail {lines} {container}")
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"📋 **Logs: `{container}` (last {lines})**\n```\n{out[:2000]}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)


class DockerStatsSkill(BaseSkill):
    name        = "docker_stats"
    description = "Show live resource usage for all running Docker containers (single snapshot)."
    platforms   = ["linux"]

    async def execute(self, **kwargs) -> SkillResult:
        rc, out = await _run("docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'")
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"📊 **Docker Stats**\n```\n{out}\n```",
                data={},
            )
        return SkillResult(success=False, output="", error=out)
