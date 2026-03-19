"""
core/text_tools.py — Nexara Skills Warehouse
Text utilities: hashing, base64, UUID, regex, diff, word count, case convert.

Dependencies: none (stdlib only)
Platforms   : all
"""

import base64
import difflib
import hashlib
import json
import re
import secrets
import string
import uuid

from skills.base import BaseSkill, SkillResult


class HashTextSkill(BaseSkill):
    name        = "hash_text"
    description = "Hash text or a file. Args: text (str), algorithm ('md5'|'sha1'|'sha256'|'sha512')."
    platforms   = ["all"]

    ALGOS = {"md5": hashlib.md5, "sha1": hashlib.sha1,
             "sha256": hashlib.sha256, "sha512": hashlib.sha512}

    async def execute(self, text: str = "", algorithm: str = "sha256", **kwargs) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        fn = self.ALGOS.get(algorithm.lower())
        if not fn:
            return SkillResult(success=False, output="", error=f"Unknown algorithm. Use: {list(self.ALGOS)}")
        digest = fn(text.encode("utf-8")).hexdigest()
        return SkillResult(
            success=True,
            output=f"🔑 **{algorithm.upper()}**\n`{digest}`",
            data={"algorithm": algorithm, "hash": digest},
        )


class Base64Skill(BaseSkill):
    name        = "base64_tool"
    description = "Encode or decode base64. Args: text (str), action ('encode'|'decode')."
    platforms   = ["all"]

    async def execute(self, text: str = "", action: str = "encode", **kwargs) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        try:
            if action == "encode":
                result = base64.b64encode(text.encode("utf-8")).decode("utf-8")
                return SkillResult(success=True, output=f"🔒 **Base64 Encoded:**\n`{result}`", data={"result": result})
            elif action == "decode":
                result = base64.b64decode(text.encode("utf-8")).decode("utf-8", errors="replace")
                return SkillResult(success=True, output=f"🔓 **Base64 Decoded:**\n{result}", data={"result": result})
            return SkillResult(success=False, output="", error="action must be 'encode' or 'decode'")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class UUIDGenSkill(BaseSkill):
    name        = "uuid_gen"
    description = "Generate UUIDs or random tokens. Args: count (int, default 1), type ('uuid4'|'uuid1'|'token_hex'|'password')."
    platforms   = ["all"]

    async def execute(self, count: int = 1, type: str = "uuid4", **kwargs) -> SkillResult:
        count   = max(1, min(20, count))
        results = []
        for _ in range(count):
            if type == "uuid4":
                results.append(str(uuid.uuid4()))
            elif type == "uuid1":
                results.append(str(uuid.uuid1()))
            elif type == "token_hex":
                results.append(secrets.token_hex(32))
            elif type == "password":
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                results.append("".join(secrets.choice(alphabet) for _ in range(20)))
            else:
                return SkillResult(success=False, output="", error=f"Unknown type. Use: uuid4, uuid1, token_hex, password")

        output = f"🎲 **Generated ({type}):**\n" + "\n".join(f"`{r}`" for r in results)
        return SkillResult(success=True, output=output, data={"results": results})


class RegexToolSkill(BaseSkill):
    name        = "regex_tool"
    description = (
        "Test, find, or replace using a regex pattern. "
        "Args: text (str), pattern (str), action ('test'|'find'|'replace'), replacement (str opt)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        text:        str = "",
        pattern:     str = "",
        action:      str = "find",
        replacement: str = "",
        **kwargs,
    ) -> SkillResult:
        if not text or not pattern:
            return SkillResult(success=False, output="", error="text and pattern are required.")
        try:
            compiled = re.compile(pattern, re.MULTILINE)
        except re.error as exc:
            return SkillResult(success=False, output="", error=f"Invalid regex: {exc}")

        if action == "test":
            match = bool(compiled.search(text))
            return SkillResult(
                success=True,
                output=f"🔍 Pattern `{pattern}` → **{'MATCH ✅' if match else 'NO MATCH ❌'}**",
                data={"match": match},
            )
        if action == "find":
            matches = compiled.findall(text)
            if not matches:
                return SkillResult(success=True, output=f"No matches found for `{pattern}`.", data={})
            lines   = [f"🔍 **{len(matches)} match(es)** for `{pattern}`:\n"]
            for i, m in enumerate(matches[:20], 1):
                lines.append(f"  {i}. `{m}`")
            return SkillResult(success=True, output="\n".join(lines), data={"matches": matches[:20]})
        if action == "replace":
            result = compiled.sub(replacement, text)
            return SkillResult(
                success=True,
                output=f"✏️ **Replaced** (`{pattern}` → `{replacement}`):\n\n{result[:2000]}",
                data={"result": result},
            )
        return SkillResult(success=False, output="", error="action must be 'test', 'find', or 'replace'")


class TextDiffSkill(BaseSkill):
    name        = "text_diff"
    description = "Show the diff between two texts. Args: text_a (str), text_b (str)."
    platforms   = ["all"]

    async def execute(self, text_a: str = "", text_b: str = "", **kwargs) -> SkillResult:
        if not text_a or not text_b:
            return SkillResult(success=False, output="", error="text_a and text_b are required.")
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff    = list(difflib.unified_diff(lines_a, lines_b, fromfile="text_a", tofile="text_b"))
        if not diff:
            return SkillResult(success=True, output="✅ Texts are identical.", data={"identical": True})
        diff_text = "".join(diff[:100])
        return SkillResult(
            success=True,
            output=f"📝 **Text Diff**\n```diff\n{diff_text}\n```",
            data={"changes": len(diff), "identical": False},
        )


class TextStatsSkill(BaseSkill):
    name        = "text_stats"
    description = "Count words, characters, lines, and sentences in text. Args: text (str)."
    platforms   = ["all"]

    async def execute(self, text: str = "", **kwargs) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        words     = len(text.split())
        chars     = len(text)
        chars_ns  = len(text.replace(" ", ""))
        lines     = text.count("\n") + 1
        sentences = len(re.findall(r'[.!?]+', text))
        paragraphs= len([p for p in text.split("\n\n") if p.strip()])
        read_min  = max(1, round(words / 200))   # avg reading speed ~200 wpm
        return SkillResult(
            success=True,
            output=(
                f"📊 **Text Statistics**\n"
                f"  Words      : {words:,}\n"
                f"  Characters : {chars:,}  ({chars_ns:,} without spaces)\n"
                f"  Lines      : {lines:,}\n"
                f"  Sentences  : {sentences:,}\n"
                f"  Paragraphs : {paragraphs:,}\n"
                f"  Read time  : ~{read_min} min"
            ),
            data={
                "words": words, "chars": chars, "lines": lines,
                "sentences": sentences, "read_minutes": read_min,
            },
        )


class CaseConverterSkill(BaseSkill):
    name        = "case_convert"
    description = (
        "Convert text case. "
        "Args: text (str), style ('upper'|'lower'|'title'|'snake'|'camel'|'kebab'|'sentence')."
    )
    platforms   = ["all"]

    async def execute(self, text: str = "", style: str = "title", **kwargs) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="No text provided.")
        if style == "upper":
            result = text.upper()
        elif style == "lower":
            result = text.lower()
        elif style == "title":
            result = text.title()
        elif style == "sentence":
            result = text[0].upper() + text[1:].lower() if text else ""
        elif style == "snake":
            result = re.sub(r'[\s\-]+', '_', text.lower())
            result = re.sub(r'[^\w_]', '', result)
        elif style == "camel":
            words  = re.split(r'[\s_\-]+', text)
            result = words[0].lower() + "".join(w.title() for w in words[1:])
        elif style == "kebab":
            result = re.sub(r'[\s_]+', '-', text.lower())
            result = re.sub(r'[^\w\-]', '', result)
        else:
            return SkillResult(success=False, output="", error=f"Unknown style: {style}")
        return SkillResult(success=True, output=f"✏️ **{style.title()}:**\n{result}", data={"result": result})
