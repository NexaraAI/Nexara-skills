"""
linux/git_ops.py — Nexara Skills Warehouse
Git operations: clone, pull, push, status, log, diff, branch.

Dependencies: git CLI
Platforms   : linux
"""

import asyncio
from pathlib import Path
from skills.base import BaseSkill, SkillResult

async def _run(cmd, cwd=None, timeout=60):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        cwd=cwd)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Timed out after {timeout}s"

class GitOpsSkill(BaseSkill):
    name        = "git_ops"
    description = (
        "Git operations on a repository. "
        "Args: action ('clone'|'pull'|'push'|'status'|'log'|'diff'|'branch'|'checkout'|'commit'), "
        "repo_url (str opt), path (str, default current dir), branch (str opt), "
        "message (str opt for commit)."
    )
    platforms   = ["linux"]

    async def execute(
        self,
        action:   str = "status",
        repo_url: str = "",
        path:     str = ".",
        branch:   str = "",
        message:  str = "",
        **kwargs,
    ):
        cwd = str(Path(path).expanduser())

        if action == "clone":
            if not repo_url:
                return SkillResult(success=False, output="", error="repo_url required for clone.")
            cmd = f"git clone {repo_url} {cwd}"
            rc, out = await _run(cmd, timeout=120)
        elif action == "pull":
            cmd = f"git pull {('origin ' + branch) if branch else ''}"
            rc, out = await _run(cmd, cwd=cwd)
        elif action == "push":
            cmd = f"git push {('origin ' + branch) if branch else ''}"
            rc, out = await _run(cmd, cwd=cwd, timeout=60)
        elif action == "status":
            rc, out = await _run("git status", cwd=cwd)
        elif action == "log":
            rc, out = await _run("git log --oneline -15", cwd=cwd)
        elif action == "diff":
            rc, out = await _run("git diff --stat HEAD~1", cwd=cwd)
        elif action == "branch":
            rc, out = await _run("git branch -a", cwd=cwd)
        elif action == "checkout":
            if not branch:
                return SkillResult(success=False, output="", error="branch required for checkout.")
            rc, out = await _run(f"git checkout {branch}", cwd=cwd)
        elif action == "commit":
            if not message:
                return SkillResult(success=False, output="", error="message required for commit.")
            rc, out = await _run(f"git add -A && git commit -m '{message}'", cwd=cwd)
        else:
            return SkillResult(success=False, output="", error=f"Unknown action: {action}")

        ok = rc == 0
        return SkillResult(
            success=ok,
            output=f"📦 **git {action}**\n```\n{out[:2000]}\n```",
            data={"returncode": rc},
            error="" if ok else out[-300:],
        )
