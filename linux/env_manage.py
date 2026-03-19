"""
linux/env_manage.py — Nexara Skills Warehouse
Read, set, and manage environment variables and .env files.

Dependencies: none
Platforms   : linux
"""

import os
import re
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class EnvManageSkill(BaseSkill):
    name        = "env_manage"
    description = (
        "Manage environment variables and .env files. "
        "Args: action ('list'|'get'|'set_env_file'|'read_env_file'), "
        "key (str opt), value (str opt), file_path (str opt), filter (str opt)."
    )
    platforms   = ["linux"]

    async def execute(
        self,
        action:    str = "list",
        key:       str = "",
        value:     str = "",
        file_path: str = "",
        filter:    str = "",
        **kwargs,
    ):
        if action == "list":
            env_vars = dict(os.environ)
            if filter:
                env_vars = {k: v for k, v in env_vars.items() if filter.upper() in k}
            # Mask sensitive keys
            masked = {}
            for k, v in sorted(env_vars.items()):
                if any(s in k.upper() for s in ("KEY", "SECRET", "PASS", "TOKEN", "CREDENTIAL")):
                    masked[k] = v[:4] + "****" if len(v) > 4 else "****"
                else:
                    masked[k] = v[:60]
            lines = [f"🔑 **Environment Variables** ({len(masked)})\n```"]
            for k, v in masked.items():
                lines.append(f"{k}={v}")
            lines.append("```")
            return SkillResult(success=True, output="\n".join(lines), data={"count": len(masked)})

        if action == "get":
            if not key:
                return SkillResult(success=False, output="", error="key required.")
            val = os.environ.get(key, None)
            if val is None:
                return SkillResult(success=True, output=f"⚠️ `{key}` is not set.", data={"set": False})
            masked = val[:4] + "****" if any(s in key.upper() for s in ("KEY","SECRET","PASS","TOKEN")) else val
            return SkillResult(success=True, output=f"🔑 `{key}` = `{masked}`", data={"key": key, "set": True})

        if action == "read_env_file":
            p = Path(file_path or ".env").expanduser()
            if not p.exists():
                return SkillResult(success=False, output="", error=f"File not found: {p}")
            lines_out = []
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith("#"):
                    k = line.split("=", 1)[0].strip()
                    if any(s in k.upper() for s in ("KEY","SECRET","PASS","TOKEN")):
                        line = f"{k}=****"
                lines_out.append(line)
            return SkillResult(
                success=True,
                output=f"📄 **`{p}`**\n```\n{\'\n\'.join(lines_out[:50])}\n```",
                data={"path": str(p)},
            )

        if action == "set_env_file":
            if not key or not value:
                return SkillResult(success=False, output="", error="key and value required.")
            p = Path(file_path or ".env").expanduser()
            content = p.read_text(encoding="utf-8") if p.exists() else ""
            lines   = content.splitlines()
            updated = False
            for i, line in enumerate(lines):
                if re.match(rf"^{re.escape(key)}\s*=", line):
                    lines[i] = f"{key}={value}"
                    updated  = True
                    break
            if not updated:
                lines.append(f"{key}={value}")
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return SkillResult(success=True, output=f"✅ `{key}` {'updated' if updated else 'added'} in `{p}`", data={})

        return SkillResult(success=False, output="", error=f"Unknown action: {action}")
