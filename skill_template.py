"""
skill_template.py — Nexara Skills Warehouse
Copy this file, rename it, and implement your skill.

Naming convention:
  File    : your_skill_name.py
  Class   : YourSkillNameSkill
  name    : "your_skill_name"   ← must match the filename stem

Platform tags (set all that apply):
  "all"     — works on every platform
  "android" — Termux/Android only
  "linux"   — Linux, Codespace, WSL, Docker
  "windows" — Windows native / WSL
  "macos"   — macOS only

Dependencies:
  List every pip package your skill needs in the module docstring.
  The agent's skill loader will warn if they're missing.
  ONLY use packages that are in requirements.txt or are stdlib.

Checklist before submitting a PR:
  [ ] platforms list is accurate
  [ ] execute() handles all error cases and returns SkillResult
  [ ] No bare `except:` — catch specific exceptions
  [ ] No blocking I/O — use asyncio.to_thread() for heavy work
  [ ] No hardcoded paths — use Path.home() or config values
  [ ] All external commands go through asyncio.create_subprocess_shell
  [ ] Tested locally with `python3 -c "import your_skill_name"`
"""

import asyncio
from skills.base import BaseSkill, SkillResult


class YourSkillNameSkill(BaseSkill):
    name        = "your_skill_name"
    description = "One sentence describing what this skill does and its key args."
    platforms   = ["all"]   # ← change to ["android"], ["linux"] etc as needed

    async def execute(
        self,
        required_arg: str = "",
        optional_arg: str = "default",
        **kwargs,                       # always accept **kwargs for forward-compat
    ) -> SkillResult:
        """
        Implement your skill here.

        Always return SkillResult:
          success=True  → output is shown to user and LLM as the observation
          success=False → error string triggers replanning in the ReAct loop
        """
        if not required_arg:
            return SkillResult(
                success=False,
                output="",
                error="required_arg is missing.",
            )

        try:
            # ── Your logic here ───────────────────────────────────────────────
            result = f"Did something with: {required_arg}, {optional_arg}"

            return SkillResult(
                success=True,
                output=result,
                data={"key": "value"},  # structured data (optional, for chaining)
            )

        except FileNotFoundError as exc:
            return SkillResult(success=False, output="", error=f"File not found: {exc}")
        except PermissionError as exc:
            return SkillResult(success=False, output="", error=f"Permission denied: {exc}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


# ── How to run a shell command safely ────────────────────────────────────────
async def _run(cmd: str, timeout: int = 30) -> tuple[int, str]:
    """Helper — run a shell command and return (exit_code, output)."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Command timed out after {timeout}s"
