"""
core/speedtest.py — Nexara Skills Warehouse
Internet speed test using speedtest-cli (pip) with a curl-based fallback.

Dependencies: httpx (always available); speedtest-cli (auto-installed if missing)
Platforms   : all
"""

import asyncio
import logging
import re
import shutil
import time

from skills.base import BaseSkill, SkillResult

logger = logging.getLogger("nexara.skill.speedtest")


class SpeedTestSkill(BaseSkill):
    name        = "speedtest"
    description = (
        "Run an internet speed test. Returns download speed, upload speed, "
        "ping, and server info. No arguments required."
    )
    platforms   = ["all"]

    async def execute(self, **kwargs) -> SkillResult:
        # ── Method 1: speedtest-cli binary ────────────────────────────────────
        if shutil.which("speedtest-cli") or shutil.which("speedtest"):
            result = await self._run_cli()
            if result.success:
                return result

        # ── Method 2: speedtest-cli Python package ────────────────────────────
        result = await self._run_python_pkg()
        if result.success:
            return result

        # ── Method 3: curl download benchmark (always works) ─────────────────
        return await self._run_curl_benchmark()

    # ── Method 1: CLI binary ──────────────────────────────────────────────────

    async def _run_cli(self) -> SkillResult:
        try:
            bin_name = "speedtest-cli" if shutil.which("speedtest-cli") else "speedtest"
            proc = await asyncio.create_subprocess_exec(
                bin_name, "--simple",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            text = stdout.decode()

            ping_m     = re.search(r"Ping:\s+([\d.]+)\s*ms",      text)
            dl_m       = re.search(r"Download:\s+([\d.]+)\s*Mbit/s", text)
            ul_m       = re.search(r"Upload:\s+([\d.]+)\s*Mbit/s",   text)

            if dl_m and ul_m:
                ping     = float(ping_m.group(1)) if ping_m else None
                download = float(dl_m.group(1))
                upload   = float(ul_m.group(1))
                return SkillResult(
                    success=True,
                    output=self._format(download, upload, ping),
                    data={"download_mbps": download, "upload_mbps": upload, "ping_ms": ping},
                )
        except Exception as exc:
            logger.debug("speedtest-cli binary failed: %s", exc)
        return SkillResult(success=False, output="", error="CLI method failed")

    # ── Method 2: Python speedtest-cli package ────────────────────────────────

    async def _run_python_pkg(self) -> SkillResult:
        def _test():
            try:
                import speedtest as st
            except ImportError:
                import subprocess, sys
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "speedtest-cli", "-q"],
                    timeout=30,
                )
                import speedtest as st

            s = st.Speedtest(secure=True)
            s.get_best_server()
            s.download(threads=4)
            s.upload(threads=4)
            r = s.results
            return {
                "download_mbps": round(r.download / 1_000_000, 2),
                "upload_mbps":   round(r.upload   / 1_000_000, 2),
                "ping_ms":       round(r.ping, 1),
                "server":        f"{r.server.get('name','?')}, {r.server.get('country','?')}",
            }

        try:
            data = await asyncio.wait_for(asyncio.to_thread(_test), timeout=90)
            return SkillResult(
                success=True,
                output=self._format(
                    data["download_mbps"],
                    data["upload_mbps"],
                    data.get("ping_ms"),
                    data.get("server"),
                ),
                data=data,
            )
        except Exception as exc:
            logger.debug("speedtest Python pkg failed: %s", exc)
        return SkillResult(success=False, output="", error="Python pkg method failed")

    # ── Method 3: curl benchmark (always available) ───────────────────────────

    async def _run_curl_benchmark(self) -> SkillResult:
        """
        Rough download benchmark using a 100 MB test file from Cloudflare.
        Not as accurate as a real speed test but never requires extra dependencies.
        """
        import httpx

        TEST_URL  = "https://speed.cloudflare.com/__down?bytes=26214400"  # 25 MB
        TEST_BYTES = 26_214_400

        try:
            t0 = time.time()
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(TEST_URL)
                data = await resp.aread()
            elapsed  = time.time() - t0
            received = len(data)
            dl_mbps  = round((received * 8) / elapsed / 1_000_000, 2)

            note = (
                "⚠️ This is a download-only benchmark (25 MB via Cloudflare). "
                "Install speedtest-cli for accurate upload + ping results."
            )
            return SkillResult(
                success=True,
                output=(
                    f"🌐 Speed Test (download benchmark)\n\n"
                    f"📥 Download : ~{dl_mbps} Mbit/s\n"
                    f"📤 Upload   : N/A (install speedtest-cli for this)\n"
                    f"⏱ Duration : {elapsed:.1f}s  ({received//1024//1024} MB received)\n\n"
                    f"{note}"
                ),
                data={"download_mbps": dl_mbps, "method": "curl_benchmark"},
            )
        except Exception as exc:
            return SkillResult(
                success=False, output="",
                error=f"All speed test methods failed: {exc}"
            )

    # ── Formatter ─────────────────────────────────────────────────────────────

    @staticmethod
    def _format(
        download: float,
        upload:   float,
        ping:     float | None = None,
        server:   str  | None  = None,
    ) -> str:
        lines = [
            "🌐 Speed Test Results\n",
            f"📥 Download : {download:.2f} Mbit/s",
            f"📤 Upload   : {upload:.2f} Mbit/s",
        ]
        if ping is not None:
            lines.append(f"📡 Ping     : {ping:.1f} ms")
        if server:
            lines.append(f"🖥️  Server   : {server}")
        return "\n".join(lines)
