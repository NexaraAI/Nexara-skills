"""
linux/ssh_exec.py — Nexara Skills Warehouse
Execute commands on remote hosts via SSH.

Dependencies: none (uses ssh CLI)
Platforms   : linux
"""

import asyncio
import re

from skills.base import BaseSkill, SkillResult

TIMEOUT = 30

# Block dangerous remote commands
_BLOCKED = ["rm -rf /", "mkfs", "shutdown", "reboot", ":(){:|:&};:"]


async def _run(cmd: str, timeout: int = TIMEOUT) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"SSH command timed out after {timeout}s"


class SSHExecSkill(BaseSkill):
    name        = "ssh_exec"
    description = (
        "Run a command on a remote host via SSH. "
        "Args: host (str), command (str), user (str opt), port (int opt, default 22), "
        "key_path (str opt)."
    )
    platforms   = ["linux"]

    async def execute(
        self,
        host:     str = "",
        command:  str = "",
        user:     str = "",
        port:     int = 22,
        key_path: str = "",
        **kwargs,
    ) -> SkillResult:
        if not host or not command:
            return SkillResult(success=False, output="", error="host and command are required.")

        for pattern in _BLOCKED:
            if pattern in command:
                return SkillResult(success=False, output="", error=f"Blocked pattern: `{pattern}`")

        target  = f"{user}@{host}" if user else host
        key_opt = f"-i {key_path}" if key_path else ""
        ssh_cmd = (
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
            f"-p {port} {key_opt} {target} '{command}'"
        )

        rc, out = await _run(ssh_cmd)
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"🔌 **SSH `{target}`**\n```\n{out[:2000]}\n```",
                data={"host": host, "returncode": rc},
            )
        return SkillResult(success=False, output="", error=out[-500:])


class SSHCopySkill(BaseSkill):
    name        = "ssh_copy"
    description = (
        "Copy a file to/from a remote host via SCP. "
        "Args: source (str), destination (str), key_path (str opt)."
    )
    platforms   = ["linux"]

    async def execute(
        self,
        source:      str = "",
        destination: str = "",
        key_path:    str = "",
        **kwargs,
    ) -> SkillResult:
        if not source or not destination:
            return SkillResult(success=False, output="", error="source and destination are required.")
        key_opt = f"-i {key_path}" if key_path else ""
        cmd     = f"scp -o StrictHostKeyChecking=no {key_opt} '{source}' '{destination}'"
        rc, out = await _run(cmd, timeout=120)
        if rc == 0:
            return SkillResult(success=True, output=f"📤 Copied `{source}` → `{destination}`", data={})
        return SkillResult(success=False, output="", error=out)
