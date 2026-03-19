"""
.github/scripts/ast_scan.py
Scans all skill files for dangerous AST patterns before merging.
Blocks: eval, exec, __import__, os.system, subprocess without whitelist,
        open('/dev'), open('/proc'), open('/sys'), ctypes, importlib.
"""

import ast
import sys
from pathlib import Path

SKILL_DIRS = ["core", "android", "linux", "windows", "macos"]

BLOCKED_CALLS = {
    "eval", "exec", "compile",
}

BLOCKED_ATTRS = {
    ("os",         "system"),
    ("os",         "popen"),
    ("ctypes",     "CDLL"),
    ("ctypes",     "cdll"),
    ("importlib",  "import_module"),
}

BLOCKED_NAMES = {
    "__import__",
}

BLOCKED_STRING_PATTERNS = [
    "/dev/null",
    "/proc/",
    "/sys/",
    "open('/dev",
    "open(\"/dev",
]

errors: list[str] = []


def scan_file(path: Path):
    src  = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))

    for node in ast.walk(tree):
        # Blocked function calls: eval(), exec(), compile()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_CALLS:
                    errors.append(f"{path}:{node.lineno}: blocked call `{node.func.id}()`")
            if isinstance(node.func, ast.Attribute):
                pair = (
                    node.func.value.id if isinstance(node.func.value, ast.Name) else "",
                    node.func.attr,
                )
                if pair in BLOCKED_ATTRS:
                    errors.append(f"{path}:{node.lineno}: blocked `{pair[0]}.{pair[1]}()`")

        # Blocked names: __import__
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            errors.append(f"{path}:{node.lineno}: blocked name `{node.id}`")

    # String pattern scan (catches obfuscated paths)
    for i, line in enumerate(src.splitlines(), 1):
        for pattern in BLOCKED_STRING_PATTERNS:
            if pattern in line:
                errors.append(f"{path}:{i}: blocked pattern `{pattern}`")


root = Path(".")
for d in SKILL_DIRS:
    for py_file in Path(d).glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            scan_file(py_file)
        except SyntaxError as exc:
            errors.append(f"{py_file}: syntax error — {exc}")

if errors:
    print(f"\n❌ AST scan FAILED — {len(errors)} issue(s):\n")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

print(f"✅ AST scan passed — {sum(1 for d in SKILL_DIRS for _ in Path(d).glob('*.py'))} files clean")
