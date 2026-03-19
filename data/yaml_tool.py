"""
data/yaml_tool.py — Nexara Skills Warehouse
Read, write, validate, and query YAML files.

Dependencies: pyyaml
Platforms   : all
"""

import asyncio
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class YamlToolSkill(BaseSkill):
    name        = "yaml_tool"
    description = (
        "Read, write, and query YAML files. "
        "Args: file_path (str opt), yaml_text (str opt), "
        "action ('read'|'validate'|'get'), key_path (str opt, dot-notation)."
    )
    platforms   = ["all"]

    async def execute(self, file_path: str = "", yaml_text: str = "", action: str = "read", key_path: str = "", **kwargs):
        def _work():
            try:
                import yaml
            except ImportError:
                return None, "pyyaml not installed. Run: pip install pyyaml"

            if file_path:
                p = Path(file_path).expanduser()
                if not p.exists():
                    return None, f"File not found: {p}"
                text = p.read_text(encoding="utf-8")
            elif yaml_text:
                text = yaml_text
            else:
                return None, "file_path or yaml_text required."

            try:
                data = yaml.safe_load(text)
            except yaml.YAMLError as exc:
                return None, f"YAML parse error: {exc}"

            if action == "validate":
                return f"✅ Valid YAML. Type: {type(data).__name__}", None

            if action == "get" and key_path:
                parts   = key_path.split(".")
                current = data
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part)
                    elif isinstance(current, list) and part.isdigit():
                        current = current[int(part)]
                    else:
                        return None, f"Key '{part}' not found."
                return yaml.dump(current, default_flow_style=False)[:2000], None

            # Default: pretty print
            return yaml.dump(data, default_flow_style=False)[:2500], None

        try:
            result, error = await asyncio.to_thread(_work)
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        if error:
            return SkillResult(success=False, output="", error=error)
        return SkillResult(
            success=True,
            output=f"📄 **YAML**{(' — '+key_path) if key_path else ''}\n```yaml\n{result}\n```",
            data={},
        )
