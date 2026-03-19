"""
core/command.py — Nexara Skills Warehouse
Whitelisted shell command execution.

Dependencies: none (stdlib only)
Platforms   : all
"""

import asyncio
import shlex

from skills.base import BaseSkill, SkillResult

WHITELIST: frozenset[str] = frozenset({
    "ls", "cat", "echo", "pwd", "whoami", "date", "uname",
    "df", "du", "free", "uptime", "top", "ps",
    "grep", "find", "sed", "awk", "cut", "sort", "uniq", "wc",
    "head", "tail", "diff", "which", "file", "stat",
    "mkdir", "touch", "cp", "mv", "chmod",
    "ping", "curl", "wget", "nc", "nslookup", "dig",
    "tar", "zip", "unzip", "gzip", "gunzip",
    "python3", "pip", "pip3", "git",
    # Android / Termux
    "am", "pm", "termux-open",
    "termux-battery-status", "termux-brightness", "termux-camera-photo",
    "termux-clipboard-get", "termux-clipboard-set", "termux-contact-list",
    "termux-dialog", "termux-download", "termux-location",
    "termux-media-player", "termux-notification", "termux-notification-list",
    "termux-phone-call", "termux-sensor", "termux-share",
    "termux-sms-list", "termux-sms-send", "termux-storage-get",
    "termux-toast", "termux-torch", "termux-tts-speak",
    "termux-vibrate", "termux-volume", "termux-wallpaper",
    "termux-wifi-connectioninfo", "termux-wifi-enable", "termux-wifi-scaninfo",
    # Linux
    "systemctl", "journalctl", "apt", "apt-get", "dpkg",
    "docker", "docker-compose", "ssh", "scp", "rsync",
    "crontab", "env", "printenv", "id", "groups",
    "lsof", "netstat", "ss", "ip", "ifconfig",
})

BLOCKED_PATTERNS: list[str] = [
    "rm -rf /", "rm -r /", "mkfs", ":(){:|:&};:",
    "dd if=/dev/zero", "chmod 777 /", "> /dev/sda",
    "shutdown", "reboot",
]

TIMEOUT_SECONDS = 30


class CommandSkill(BaseSkill):
    name        = "command"
    description = "Execute a whitelisted shell command and return stdout."
    platforms   = ["all"]

    async def execute(self, command: str = "", **kwargs) -> SkillResult:
        if not command:
            return SkillResult(success=False, output="", error="No command provided.")

        for pattern in BLOCKED_PATTERNS:
            if pattern in command:
                return SkillResult(
                    success=False, output="",
                    error=f"Blocked — forbidden pattern: `{pattern}`",
                )

        try:
            parts    = shlex.split(command)
            root_cmd = parts[0] if parts else ""
        except ValueError as exc:
            return SkillResult(success=False, output="", error=f"Parse error: {exc}")

        if root_cmd not in WHITELIST:
            return SkillResult(
                success=False, output="",
                error=(
                    f"`{root_cmd}` is not in the command whitelist. "
                    "Add it in core/command.py WHITELIST."
                ),
            )

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT_SECONDS)
            output    = stdout.decode("utf-8", errors="replace").strip()
            success   = proc.returncode == 0
            return SkillResult(
                success=success,
                output=output or "(no output)",
                data={"returncode": proc.returncode},
                error="" if success else f"Exit code {proc.returncode}",
            )
        except asyncio.TimeoutError:
            return SkillResult(success=False, output="", error=f"Timed out after {TIMEOUT_SECONDS}s")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
