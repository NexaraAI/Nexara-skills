"""
core/code_exec.py — Nexara Skills Warehouse
Run Python code in an isolated subprocess with memory + time limits.

Dependencies: none (stdlib only)
Platforms   : all
"""

import asyncio
import os
import sys
import tempfile
import textwrap
from pathlib import Path

from skills.base import BaseSkill, SkillResult

SCRIPTS_DIR      = Path.home() / ".nexara" / "scripts"
DEFAULT_TIMEOUT  = 30
MAX_MEM_MB       = 256
MAX_OUTPUT_CHARS = 4000

_RUNNER = """\
import sys, os
sys.setrecursionlimit(500)
import json, re, math, time, datetime, pathlib, hashlib, shutil
from pathlib import Path
from datetime import datetime, timedelta

{user_code}
"""

_BLOCKED = [
    "import socket", "__import__(", "importlib", "ctypes",
    "os.system", "subprocess.Popen", "subprocess.run", "subprocess.call",
    "open('/dev", "open('/proc", "open('/sys", "/dev/null",
]


def _ulimit() -> str:
    return f"ulimit -v {MAX_MEM_MB * 1024} 2>/dev/null; "


class RunCodeSkill(BaseSkill):
    name        = "run_code"
    description = (
        "Execute Python code in an isolated subprocess. "
        "Args: code (str), save_as (str opt), timeout (int opt, default 30)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        code:    str = "",
        save_as: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> SkillResult:
        if not code:
            return SkillResult(success=False, output="", error="No code provided.")
        timeout = min(max(timeout, 1), 120)

        for pattern in _BLOCKED:
            if pattern in code:
                return SkillResult(success=False, output="", error=f"Blocked: `{pattern}`")

        full_script = textwrap.dedent(_RUNNER.format(user_code=textwrap.dedent(code)))
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=SCRIPTS_DIR,
            delete=False, prefix="exec_"
        ) as tf:
            tf.write(full_script)
            tmp_path = tf.name

        if save_as:
            named = SCRIPTS_DIR / (save_as if save_as.endswith(".py") else f"{save_as}.py")
            named.write_text(textwrap.dedent(code), encoding="utf-8")

        try:
            cmd  = f"{_ulimit()}{sys.executable} '{tmp_path}'"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return SkillResult(
                    success=False, output="",
                    error=f"⏱️ Timed out after {timeout}s.",
                )

            out = stdout.decode("utf-8", errors="replace").strip()
            err = stderr.decode("utf-8", errors="replace").strip()
            ok  = proc.returncode == 0

            parts = []
            if out: parts.append(f"**Output:**\n```\n{out[:MAX_OUTPUT_CHARS]}\n```")
            if err: parts.append(f"**{'Error' if not ok else 'Stderr'}:**\n```\n{err[:1000]}\n```")
            if not parts: parts.append("✅ Executed with no output.")

            return SkillResult(
                success=ok,
                output="\n\n".join(parts),
                data={"returncode": proc.returncode, "saved_as": save_as or None},
                error=err if not ok else "",
            )
        finally:
            try: Path(tmp_path).unlink()
            except Exception: pass


class ListScriptsSkill(BaseSkill):
    name        = "list_scripts"
    description = "List all Python scripts saved by the agent."
    platforms   = ["all"]

    async def execute(self, **kwargs) -> SkillResult:
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        scripts = sorted(
            (f for f in SCRIPTS_DIR.glob("*.py") if not f.name.startswith("exec_")),
            key=lambda f: f.stat().st_mtime, reverse=True,
        )
        if not scripts:
            return SkillResult(success=True, output="No scripts saved yet.", data={})
        lines = [f"🐍 **Saved Scripts** (`{SCRIPTS_DIR}`)\n"]
        for s in scripts:
            lines.append(f"• `{s.name}` — {s.stat().st_size} bytes")
        return SkillResult(success=True, output="\n".join(lines), data={})
