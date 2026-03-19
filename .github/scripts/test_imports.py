"""
.github/scripts/test_imports.py
Attempts to import every skill file in isolation.
Catches import errors, missing dependencies, and syntax errors early.
"""

import importlib.util
import sys
from pathlib import Path

SKILL_DIRS = ["core", "android", "linux", "windows", "macos"]

# Stub BaseSkill so we don't need the full agent codebase
import types

stub_module = types.ModuleType("skills.base")

class _StubResult:
    def __init__(self, *a, **kw): pass

class _StubMeta(type):
    _registry = {}
    def __new__(mcs, name, bases, ns, **kw):
        cls = super().__new__(mcs, name, bases, ns)
        if bases:
            skill_name = ns.get("name", "")
            if skill_name:
                mcs._registry[skill_name] = cls
        return cls

class _StubBase(metaclass=_StubMeta):
    name = ""
    description = ""
    platforms = ["all"]
    async def execute(self, **kwargs):
        return _StubResult()

stub_module.SkillResult = _StubResult
stub_module.BaseSkill   = _StubBase
stub_module.SkillMeta   = _StubMeta
sys.modules["skills"]       = types.ModuleType("skills")
sys.modules["skills.base"]  = stub_module

errors:  list[str] = []
success: int       = 0

for d in SKILL_DIRS:
    for py_file in sorted(Path(d).glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        mod_name = f"skill_test.{d}.{py_file.stem}"
        try:
            spec   = importlib.util.spec_from_file_location(mod_name, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            success += 1
        except ImportError as exc:
            # Missing optional deps (PIL, pdfplumber, etc.) are warnings, not errors
            if any(ok in str(exc) for ok in ["PIL", "pdfplumber", "psutil"]):
                print(f"  ⚠️  {py_file}: optional dep missing ({exc}) — skipping")
                success += 1
            else:
                errors.append(f"{py_file}: ImportError — {exc}")
        except Exception as exc:
            errors.append(f"{py_file}: {type(exc).__name__} — {exc}")

if errors:
    print(f"\n❌ Import test FAILED — {len(errors)} error(s):\n")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

print(f"✅ Import test passed — {success} file(s) importable")
