"""
linux/python_env.py — Nexara Skills Warehouse
Python virtual environment and pip package management.

Dependencies: python3, pip
Platforms   : linux
"""

import asyncio
import sys
from pathlib import Path
from skills.base import BaseSkill, SkillResult

async def _run(cmd, timeout=120):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"

class PythonEnvSkill(BaseSkill):
    name        = "python_env"
    description = (
        "Manage Python packages and virtual environments. "
        "Args: action ('install'|'uninstall'|'list'|'create_venv'|'pip_info'), "
        "package (str opt), venv_path (str opt)."
    )
    platforms   = ["linux"]

    async def execute(self, action: str = "list", package: str = "", venv_path: str = "", **kwargs):
        pip = f"{sys.executable} -m pip"

        if action == "install":
            if not package:
                return SkillResult(success=False, output="", error="package required.")
            rc, out = await _run(f"{pip} install {package}")
            return SkillResult(success=rc==0, output=f"📦 {out[:1000]}", data={}, error="" if rc==0 else out[-200:])

        if action == "uninstall":
            if not package:
                return SkillResult(success=False, output="", error="package required.")
            rc, out = await _run(f"{pip} uninstall -y {package}")
            return SkillResult(success=rc==0, output=f"🗑️ {out[:500]}", data={}, error="" if rc==0 else out[-200:])

        if action == "list":
            rc, out = await _run(f"{pip} list --format=columns")
            return SkillResult(success=rc==0, output=f"📋 **Installed packages**\n```\n{out[:2000]}\n```", data={})

        if action == "create_venv":
            path = venv_path or "./venv"
            rc, out = await _run(f"{sys.executable} -m venv {path}")
            if rc == 0:
                return SkillResult(success=True, output=f"✅ Virtualenv created at `{path}`\nActivate: `source {path}/bin/activate`", data={})
            return SkillResult(success=False, output="", error=out)

        if action == "pip_info":
            rc, out = await _run(f"{pip} --version")
            rc2, out2 = await _run(f"{sys.executable} --version")
            return SkillResult(success=True, output=f"🐍 {out2}\n📦 {out}", data={})

        return SkillResult(success=False, output="", error=f"Unknown action: {action}")
