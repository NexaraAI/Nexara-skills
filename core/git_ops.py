"""
core/git_ops.py — Nexara Skills Warehouse
Git repository operations: status, log, diff, commit, push, pull, clone, branch.

Dependencies: none (uses git CLI)
Platforms   : all
"""

import asyncio
from pathlib import Path

from skills.base import BaseSkill, SkillResult

TIMEOUT = 60


async def _git(cmd: str, cwd: str = "", timeout: int = TIMEOUT) -> tuple[int, str]:
    full_cmd = f"git {cmd}"
    proc = await asyncio.create_subprocess_shell(
        full_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd or None,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Git command timed out after {timeout}s"


def _resolve(repo_path: str) -> str:
    return str(Path(repo_path).expanduser().resolve()) if repo_path else ""


class GitStatusSkill(BaseSkill):
    name        = "git_status"
    description = "Show git status and recent log for a repository. Args: repo_path (str)."
    platforms   = ["all"]

    async def execute(self, repo_path: str = ".", **kwargs) -> SkillResult:
        cwd = _resolve(repo_path)
        rc, status = await _git("status --short --branch", cwd)
        if rc != 0:
            return SkillResult(success=False, output="", error=status)
        _, log = await _git("log --oneline -10", cwd)
        _, remote = await _git("remote -v", cwd)
        output = (
            f"📁 **Git Status** (`{cwd}`)\n```\n{status}\n```\n\n"
            f"**Recent commits:**\n```\n{log or '(no commits)'}\n```"
        )
        if remote:
            output += f"\n\n**Remotes:**\n```\n{remote}\n```"
        return SkillResult(success=True, output=output, data={"cwd": cwd})


class GitCommitSkill(BaseSkill):
    name        = "git_commit"
    description = "Stage all changes and commit with a message. Args: repo_path (str), message (str), push (bool, default False)."
    platforms   = ["all"]

    async def execute(
        self,
        repo_path: str  = ".",
        message:   str  = "",
        push:      bool = False,
        **kwargs,
    ) -> SkillResult:
        if not message:
            return SkillResult(success=False, output="", error="No commit message provided.")
        cwd     = _resolve(repo_path)
        rc, out = await _git("add -A", cwd)
        if rc != 0:
            return SkillResult(success=False, output="", error=f"git add failed: {out}")
        # Check if there's anything to commit
        _, diff = await _git("diff --cached --stat", cwd)
        if not diff:
            return SkillResult(success=True, output="✅ Nothing to commit — working tree clean.", data={})
        rc, out = await _git(f'commit -m "{message}"', cwd)
        if rc != 0:
            return SkillResult(success=False, output="", error=out)
        result = f"✅ **Committed:** _{message}_\n```\n{out}\n```"
        if push:
            rc2, out2 = await _git("push", cwd, timeout=120)
            if rc2 == 0:
                result += f"\n\n✅ **Pushed successfully.**"
            else:
                result += f"\n\n⚠️ **Push failed:**\n```\n{out2}\n```"
        return SkillResult(success=True, output=result, data={"message": message, "pushed": push})


class GitPullSkill(BaseSkill):
    name        = "git_pull"
    description = "Pull latest changes from remote. Args: repo_path (str), remote (str, default 'origin'), branch (str opt)."
    platforms   = ["all"]

    async def execute(
        self,
        repo_path: str = ".",
        remote:    str = "origin",
        branch:    str = "",
        **kwargs,
    ) -> SkillResult:
        cwd     = _resolve(repo_path)
        cmd     = f"pull {remote} {branch}".strip()
        rc, out = await _git(cmd, cwd, timeout=120)
        if rc == 0:
            return SkillResult(success=True, output=f"⬇️ **Git Pull**\n```\n{out}\n```", data={})
        return SkillResult(success=False, output="", error=out)


class GitCloneSkill(BaseSkill):
    name        = "git_clone"
    description = "Clone a repository. Args: url (str), dest (str opt), depth (int opt, for shallow clone)."
    platforms   = ["all"]

    async def execute(
        self,
        url:   str = "",
        dest:  str = "",
        depth: int = 0,
        **kwargs,
    ) -> SkillResult:
        if not url:
            return SkillResult(success=False, output="", error="No URL provided.")
        cmd = f"clone"
        if depth > 0:
            cmd += f" --depth {depth}"
        cmd += f" {url}"
        if dest:
            cmd += f" {dest}"
        rc, out = await _git(cmd, timeout=300)
        if rc == 0:
            return SkillResult(success=True, output=f"📥 **Git Clone**\n```\n{out}\n```", data={"url": url})
        return SkillResult(success=False, output="", error=out)


class GitBranchSkill(BaseSkill):
    name        = "git_branch"
    description = "List, create, or switch branches. Args: repo_path (str), action ('list'|'create'|'switch'|'delete'), branch_name (str opt)."
    platforms   = ["all"]

    async def execute(
        self,
        repo_path:   str = ".",
        action:      str = "list",
        branch_name: str = "",
        **kwargs,
    ) -> SkillResult:
        cwd = _resolve(repo_path)
        if action == "list":
            rc, out = await _git("branch -a", cwd)
        elif action == "create":
            if not branch_name:
                return SkillResult(success=False, output="", error="branch_name required.")
            rc, out = await _git(f"checkout -b {branch_name}", cwd)
        elif action == "switch":
            if not branch_name:
                return SkillResult(success=False, output="", error="branch_name required.")
            rc, out = await _git(f"checkout {branch_name}", cwd)
        elif action == "delete":
            if not branch_name:
                return SkillResult(success=False, output="", error="branch_name required.")
            rc, out = await _git(f"branch -d {branch_name}", cwd)
        else:
            return SkillResult(success=False, output="", error="action must be list/create/switch/delete")

        if rc == 0:
            return SkillResult(success=True, output=f"🌿 **git branch {action}**\n```\n{out}\n```", data={})
        return SkillResult(success=False, output="", error=out)


class GitDiffSkill(BaseSkill):
    name        = "git_diff"
    description = "Show diff of unstaged or staged changes. Args: repo_path (str), staged (bool, default False), file (str opt)."
    platforms   = ["all"]

    async def execute(
        self,
        repo_path: str  = ".",
        staged:    bool = False,
        file:      str  = "",
        **kwargs,
    ) -> SkillResult:
        cwd  = _resolve(repo_path)
        cmd  = "diff"
        if staged: cmd += " --cached"
        if file:   cmd += f" -- {file}"
        rc, out = await _git(cmd, cwd)
        if not out:
            return SkillResult(success=True, output="✅ No changes.", data={})
        return SkillResult(
            success=True,
            output=f"📝 **Git Diff**\n```diff\n{out[:3000]}\n```",
            data={},
        )
