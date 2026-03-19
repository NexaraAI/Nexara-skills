"""
core/base64_tool.py — Nexara Skills Warehouse
Encode/decode base64, URL-safe base64, and hex.

Dependencies: none (stdlib base64)
Platforms   : all
"""

import base64
from skills.base import BaseSkill, SkillResult


class Base64ToolSkill(BaseSkill):
    name        = "base64_tool"
    description = (
        "Encode or decode base64/hex. "
        "Args: text (str), mode ('encode'|'decode'|'encode_url'|'decode_url'|'to_hex'|'from_hex')."
    )
    platforms   = ["all"]

    async def execute(self, text: str = "", mode: str = "encode", **kwargs):
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        try:
            if mode == "encode":
                result = base64.b64encode(text.encode()).decode()
            elif mode == "decode":
                result = base64.b64decode(text.encode()).decode(errors="replace")
            elif mode == "encode_url":
                result = base64.urlsafe_b64encode(text.encode()).decode()
            elif mode == "decode_url":
                result = base64.urlsafe_b64decode(text.encode() + b"==").decode(errors="replace")
            elif mode == "to_hex":
                result = text.encode().hex()
            elif mode == "from_hex":
                result = bytes.fromhex(text).decode(errors="replace")
            else:
                return SkillResult(success=False, output="", error=f"Unknown mode: {mode}")

            return SkillResult(
                success=True,
                output=f"🔄 **{mode}**\n\nInput:  `{text[:100]}`\nOutput: `{result[:500]}`",
                data={"result": result, "mode": mode},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
