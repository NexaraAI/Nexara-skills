"""
core/image_tools.py — Nexara Skills Warehouse
Image processing: resize, compress, convert, thumbnail, rotate, crop.

Dependencies: Pillow
Platforms   : all
"""

import asyncio
import time
from pathlib import Path

from skills.base import BaseSkill, SkillResult


def _human(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


class ImageResizeSkill(BaseSkill):
    name        = "image_resize"
    description = (
        "Resize an image. "
        "Args: path (str), width (int), height (int opt — keeps aspect ratio if omitted), "
        "output_path (str opt), quality (int 1-100, default 85)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        path:        str = "",
        width:       int = 0,
        height:      int = 0,
        output_path: str = "",
        quality:     int = 85,
        **kwargs,
    ) -> SkillResult:
        if not path or not width:
            return SkillResult(success=False, output="", error="path and width are required.")

        def _resize():
            from PIL import Image
            img = Image.open(path)
            orig_w, orig_h = img.size
            if not height:
                ratio  = width / orig_w
                new_h  = int(orig_h * ratio)
            else:
                new_h  = height
            img_r  = img.resize((width, new_h), Image.LANCZOS)
            p      = Path(path)
            out    = output_path or str(p.parent / f"{p.stem}_resized{p.suffix}")
            fmt    = img.format or "JPEG"
            kw     = {"quality": quality, "optimize": True} if fmt in ("JPEG", "WEBP") else {}
            img_r.save(out, format=fmt, **kw)
            return out, (orig_w, orig_h), (width, new_h)

        try:
            out, orig, new = await asyncio.to_thread(_resize)
            orig_sz = Path(path).stat().st_size
            new_sz  = Path(out).stat().st_size
            return SkillResult(
                success=True,
                output=(
                    f"🖼️ **Image Resized**\n"
                    f"  {orig[0]}×{orig[1]} → {new[0]}×{new[1]}\n"
                    f"  {_human(orig_sz)} → {_human(new_sz)}\n"
                    f"📁 `{out}`"
                ),
                data={"path": out, "width": new[0], "height": new[1]},
            )
        except ImportError:
            return SkillResult(success=False, output="", error="Install Pillow: pip install Pillow")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class ImageConvertSkill(BaseSkill):
    name        = "image_convert"
    description = (
        "Convert an image to a different format. "
        "Args: path (str), format ('png'|'jpg'|'webp'|'gif'|'bmp'), "
        "output_path (str opt), quality (int 1-100, default 90)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        path:        str = "",
        format:      str = "jpg",
        output_path: str = "",
        quality:     int = 90,
        **kwargs,
    ) -> SkillResult:
        if not path:
            return SkillResult(success=False, output="", error="No path provided.")
        fmt    = format.lower().strip(".")
        fmt_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG",
                   "webp": "WEBP", "gif": "GIF", "bmp": "BMP"}
        pil_fmt = fmt_map.get(fmt)
        if not pil_fmt:
            return SkillResult(success=False, output="", error=f"Unsupported format: {fmt}")

        def _convert():
            from PIL import Image
            img = Image.open(path).convert("RGB" if pil_fmt == "JPEG" else "RGBA"
                                           if pil_fmt == "PNG" else "RGB")
            p   = Path(path)
            out = output_path or str(p.parent / f"{p.stem}.{fmt}")
            kw  = {"quality": quality, "optimize": True} if pil_fmt in ("JPEG", "WEBP") else {}
            img.save(out, format=pil_fmt, **kw)
            return out

        try:
            out = await asyncio.to_thread(_convert)
            return SkillResult(
                success=True,
                output=f"🖼️ Converted to **{fmt.upper()}**\n📁 `{out}`",
                data={"path": out, "format": fmt},
            )
        except ImportError:
            return SkillResult(success=False, output="", error="Install Pillow: pip install Pillow")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class ImageInfoSkill(BaseSkill):
    name        = "image_info"
    description = "Get detailed information about an image file. Args: path (str)."
    platforms   = ["all"]

    async def execute(self, path: str = "", **kwargs) -> SkillResult:
        if not path:
            return SkillResult(success=False, output="", error="No path provided.")

        def _info():
            from PIL import Image, ExifTags
            p   = Path(path)
            img = Image.open(path)
            info = {
                "filename": p.name,
                "format":   img.format,
                "mode":     img.mode,
                "size":     f"{img.width}×{img.height}",
                "file_size": _human(p.stat().st_size),
            }
            # Extract EXIF if available
            exif = {}
            try:
                raw_exif = img._getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if isinstance(value, (str, int, float)):
                            exif[str(tag)] = str(value)
            except Exception:
                pass
            return info, exif

        try:
            info, exif = await asyncio.to_thread(_info)
            lines = ["🖼️ **Image Info**\n"]
            for k, v in info.items():
                lines.append(f"  {k.replace('_',' ').title():<12}: {v}")
            if exif:
                lines.append("\n**EXIF Data:**")
                for k, v in list(exif.items())[:10]:
                    lines.append(f"  {k:<20}: {v[:60]}")
            return SkillResult(success=True, output="\n".join(lines), data={**info, "exif": exif})
        except ImportError:
            return SkillResult(success=False, output="", error="Install Pillow: pip install Pillow")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
