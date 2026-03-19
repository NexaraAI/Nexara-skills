"""
.github/scripts/interface_check.py
Verifies every skill class in the warehouse:
  - Extends BaseSkill
  - Has a non-empty `name` str attribute
  - Has a non-empty `description` str attribute
  - Has a `platforms` list attribute
  - Implements async `execute(**kwargs) -> SkillResult`
"""

import ast
import sys
from pathlib import Path

SKILL_DIRS = ["core", "android", "linux", "windows", "macos"]
errors: list[str] = []
checked = 0


def check_file(path: Path):
    global checked
    src  = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Only classes that inherit BaseSkill
        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
        if "BaseSkill" not in bases:
            continue

        checked += 1
        cls_name = node.name

        attrs   = {}
        methods = {}

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attrs[target.id] = item.value
            if isinstance(item, (ast.AsyncFunctionDef, ast.FunctionDef)):
                methods[item.name] = item

        # Check name
        if "name" not in attrs:
            errors.append(f"{path}: `{cls_name}` missing `name` attribute")
        else:
            val = attrs["name"]
            if not (isinstance(val, ast.Constant) and isinstance(val.value, str) and val.value):
                errors.append(f"{path}: `{cls_name}.name` must be a non-empty string")

        # Check description
        if "description" not in attrs:
            errors.append(f"{path}: `{cls_name}` missing `description` attribute")
        else:
            val = attrs["description"]
            if not (isinstance(val, ast.Constant) and isinstance(val.value, str) and val.value):
                errors.append(f"{path}: `{cls_name}.description` must be a non-empty string")

        # Check platforms
        if "platforms" not in attrs:
            errors.append(f"{path}: `{cls_name}` missing `platforms` list")
        else:
            val = attrs["platforms"]
            if not isinstance(val, ast.List):
                errors.append(f"{path}: `{cls_name}.platforms` must be a list")

        # Check execute method
        if "execute" not in methods:
            errors.append(f"{path}: `{cls_name}` missing `execute()` method")
        else:
            m = methods["execute"]
            if not isinstance(m, ast.AsyncFunctionDef):
                errors.append(f"{path}: `{cls_name}.execute()` must be async")
            # Check **kwargs present
            has_kwargs = m.args.vararg is None and m.args.kwarg is not None
            if not has_kwargs:
                errors.append(f"{path}: `{cls_name}.execute()` must accept **kwargs")


root = Path(".")
for d in SKILL_DIRS:
    for py_file in Path(d).glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            check_file(py_file)
        except SyntaxError as exc:
            errors.append(f"{py_file}: syntax error — {exc}")

if errors:
    print(f"\n❌ Interface check FAILED — {len(errors)} issue(s):\n")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

print(f"✅ Interface check passed — {checked} skill class(es) verified")
