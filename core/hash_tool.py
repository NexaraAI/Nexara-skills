"""
core/hash_tool.py — Nexara Skills Warehouse
Compute hashes for strings or files. MD5, SHA256, SHA512.

Dependencies: none (stdlib hashlib)
Platforms   : all
"""

import asyncio
import hashlib
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class HashToolSkill(BaseSkill):
    name        = "hash_tool"
    description = (
        "Compute MD5/SHA256/SHA512 hash of a string or file. "
        "Args: text (str opt), file_path (str opt), algorithm ('md5'|'sha256'|'sha512', default 'sha256')."
    )
    platforms   = ["all"]

    async def execute(self, text: str = "", file_path: str = "", algorithm: str = "sha256", **kwargs):
        algo = algorithm.lower().replace("-", "")
        if algo not in ("md5", "sha256", "sha512"):
            return SkillResult(success=False, output="", error=f"Unsupported algorithm: {algorithm}")
        h = hashlib.new(algo)

        if file_path:
            p = Path(file_path).expanduser()
            if not p.exists():
                return SkillResult(success=False, output="", error=f"File not found: {p}")
            def _hash():
                hf = hashlib.new(algo)
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        hf.update(chunk)
                return hf.hexdigest()
            digest = await asyncio.to_thread(_hash)
            return SkillResult(
                success=True,
                output=f"🔑 **{algo.upper()}** hash of `{p.name}`:\n`{digest}`",
                data={"hash": digest, "algorithm": algo, "file": str(p)},
            )

        if text:
            h.update(text.encode("utf-8"))
            digest = h.hexdigest()
            return SkillResult(
                success=True,
                output=f"🔑 **{algo.upper()}**:\n`{digest}`",
                data={"hash": digest, "algorithm": algo},
            )

        return SkillResult(success=False, output="", error="Provide text or file_path.")
