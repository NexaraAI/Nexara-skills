"""
.github/scripts/manifest_check.py
Verifies manifest.json:
  - Valid JSON
  - Every skill entry has required fields
  - Every referenced file actually exists
  - Checksums match actual file content
"""

import hashlib
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {"category", "version", "file", "checksum", "platforms", "description"}
errors: list[str] = []

try:
    manifest = json.loads(Path("manifest.json").read_text())
except (FileNotFoundError, json.JSONDecodeError) as exc:
    print(f"❌ manifest.json invalid: {exc}")
    sys.exit(1)

skills = manifest.get("skills", {})
if not skills:
    print("❌ manifest.json has no skills")
    sys.exit(1)

for skill_id, meta in skills.items():
    # Required fields
    missing = REQUIRED_FIELDS - set(meta.keys())
    if missing:
        errors.append(f"Skill `{skill_id}`: missing fields {missing}")
        continue

    # File exists
    skill_file = Path(meta["file"])
    if not skill_file.exists():
        errors.append(f"Skill `{skill_id}`: file `{meta['file']}` not found")
        continue

    # Checksum matches
    actual   = "sha256:" + hashlib.sha256(skill_file.read_bytes()).hexdigest()
    expected = meta["checksum"]
    if actual != expected:
        errors.append(
            f"Skill `{skill_id}`: checksum mismatch\n"
            f"  expected: {expected}\n"
            f"  actual  : {actual}"
        )

    # Platforms is a list
    if not isinstance(meta.get("platforms"), list) or not meta["platforms"]:
        errors.append(f"Skill `{skill_id}`: `platforms` must be a non-empty list")

if errors:
    print(f"\n❌ Manifest check FAILED — {len(errors)} issue(s):\n")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

print(f"✅ Manifest check passed — {len(skills)} skill(s) verified")
