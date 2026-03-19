"""
.github/scripts/regenerate_manifest.py
Run on every merge to main. Recomputes checksums and bumps the
`updated` timestamp in manifest.json without touching versions.
"""

import hashlib
import json
from datetime import date
from pathlib import Path

manifest_path = Path("manifest.json")
manifest      = json.loads(manifest_path.read_text())

sha_lines: list[str] = []

for skill_id, meta in manifest["skills"].items():
    skill_file = Path(meta["file"])
    if not skill_file.exists():
        print(f"  WARNING: {skill_file} missing — skipping checksum update")
        continue
    checksum = "sha256:" + hashlib.sha256(skill_file.read_bytes()).hexdigest()
    meta["checksum"] = checksum
    sha_lines.append(f"{checksum.replace('sha256:', '')}  {meta['file']}")

manifest["updated"] = date.today().isoformat()

manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
Path("checksums.sha256").write_text("\n".join(sorted(sha_lines)) + "\n")

print(f"✅ Manifest regenerated — {len(manifest['skills'])} skills, updated={manifest['updated']}")
