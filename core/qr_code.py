"""
core/qr_code.py — Nexara Skills Warehouse
Generate QR codes as PNG files. No API key — pure Python.

Dependencies: qrcode, Pillow
Platforms   : all
"""

import asyncio
import time
from pathlib import Path

from skills.base import BaseSkill, SkillResult

OUTPUT_DIR = Path.home() / "nexara_downloads" / "qrcodes"


class QRCodeSkill(BaseSkill):
    name        = "qr_code"
    description = (
        "Generate a QR code image from any text or URL. "
        "Args: content (str), size (int 1-40, default 10), "
        "error_correction ('L'|'M'|'Q'|'H', default 'M')."
    )
    platforms   = ["all"]

    async def execute(
        self,
        content:          str = "",
        size:             int = 10,
        error_correction: str = "M",
        **kwargs,
    ) -> SkillResult:
        if not content:
            return SkillResult(success=False, output="", error="No content provided.")

        size = max(1, min(40, size))

        def _generate():
            import qrcode
            ec_map = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H,
            }
            ec = ec_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_M)
            qr = qrcode.QRCode(version=None, error_correction=ec, box_size=size, border=4)
            qr.add_data(content)
            qr.make(fit=True)
            img  = qr.make_image(fill_color="black", back_color="white")
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            filename = OUTPUT_DIR / f"qr_{int(time.time())}.png"
            img.save(str(filename))
            return str(filename)

        try:
            path = await asyncio.to_thread(_generate)
            preview = content[:60] + ("…" if len(content) > 60 else "")
            return SkillResult(
                success=True,
                output=f"📱 **QR Code generated**\nContent: `{preview}`\n📁 `{path}`",
                data={"path": path, "content": content},
            )
        except ImportError:
            return SkillResult(
                success=False, output="",
                error="Install qrcode: `pip install qrcode[pil]`",
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
