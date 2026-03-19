"""
data/xml_parse.py — Nexara Skills Warehouse
Parse XML files and run XPath-like queries.

Dependencies: none (stdlib xml.etree.ElementTree)
Platforms   : all
"""

import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from skills.base import BaseSkill, SkillResult


class XmlParseSkill(BaseSkill):
    name        = "xml_parse"
    description = (
        "Parse and query XML files or strings. "
        "Args: file_path (str opt), xml_text (str opt), "
        "xpath (str opt, e.g. './/item/title'), show_tree (bool, default False)."
    )
    platforms   = ["all"]

    async def execute(self, file_path: str = "", xml_text: str = "", xpath: str = "", show_tree: bool = False, **kwargs):
        def _parse():
            if file_path:
                p = Path(file_path).expanduser()
                if not p.exists():
                    return None, f"File not found: {p}"
                tree = ET.parse(str(p))
                root = tree.getroot()
            elif xml_text:
                root = ET.fromstring(xml_text)
            else:
                return None, "file_path or xml_text required."

            if xpath:
                elements = root.findall(xpath)
                if not elements:
                    return f"No elements matched XPath: `{xpath}`", None
                lines = [f"🔍 **XPath: `{xpath}`** — {len(elements)} match(es)\n"]
                for el in elements[:20]:
                    text = el.text.strip() if el.text else ""
                    attrs = " ".join(f"{k}='{v}'" for k, v in el.attrib.items())
                    lines.append(f"  <{el.tag}{(' '+attrs) if attrs else ''}>  {text[:80]}")
                return "\n".join(lines), None

            if show_tree:
                def _tree(el, indent=0):
                    prefix = "  " * indent
                    text   = el.text.strip()[:40] if el.text and el.text.strip() else ""
                    yield f"{prefix}<{el.tag}> {text}"
                    for child in el:
                        yield from _tree(child, indent+1)
                lines = list(_tree(root))[:50]
                return "\n".join(lines), None

            # Default: show root info
            children = list(root)
            info = (
                f"📄 **XML Root: `<{root.tag}>`**\n"
                f"  Attributes: {root.attrib}\n"
                f"  Children: {len(children)} elements\n"
                f"  Tags: {list(set(c.tag for c in children))[:10]}"
            )
            return info, None

        try:
            result, error = await asyncio.to_thread(_parse)
        except ET.ParseError as exc:
            return SkillResult(success=False, output="", error=f"XML parse error: {exc}")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

        if error:
            return SkillResult(success=False, output="", error=error)
        return SkillResult(success=True, output=result[:2500], data={})
