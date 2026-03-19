"""
core/ip_tools.py — Nexara Skills Warehouse
IP address lookup, DNS resolution, WHOIS, ping, and traceroute.

Dependencies: httpx
Platforms   : all
"""

import asyncio
import re
import socket

import httpx

from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(10, read=15, write=10, pool=10)


async def _run(cmd: str, timeout: int = 15) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, out.decode("utf-8", errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timed out"


class MyIPSkill(BaseSkill):
    name        = "my_ip"
    description = "Get the device's public IP address and geolocation info."
    platforms   = ["all"]

    async def execute(self, **kwargs) -> SkillResult:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get("https://ipinfo.io/json")
                resp.raise_for_status()
            data = resp.json()
            ip   = data.get("ip", "?")
            org  = data.get("org", "?")
            city = data.get("city", "?")
            reg  = data.get("region", "?")
            cty  = data.get("country", "?")
            tz   = data.get("timezone", "?")
            return SkillResult(
                success=True,
                output=(
                    f"🌐 **My Public IP**\n"
                    f"  IP       : `{ip}`\n"
                    f"  Location : {city}, {reg}, {cty}\n"
                    f"  ISP      : {org}\n"
                    f"  Timezone : {tz}"
                ),
                data=data,
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class IPLookupSkill(BaseSkill):
    name        = "ip_lookup"
    description = "Look up info for any IP address or domain. Args: target (str)."
    platforms   = ["all"]

    async def execute(self, target: str = "", **kwargs) -> SkillResult:
        if not target:
            return SkillResult(success=False, output="", error="No target provided.")
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"https://ipinfo.io/{target}/json")
                resp.raise_for_status()
            data = resp.json()
            if "bogon" in data or not data.get("ip"):
                return SkillResult(success=False, output="", error=f"`{target}` is a private/bogon IP")
            lines = [f"🔍 **IP Lookup: `{data.get('ip')}`**\n"]
            field_map = {
                "hostname": "Hostname", "org": "ISP/Org", "city": "City",
                "region": "Region", "country": "Country", "timezone": "Timezone",
                "loc": "Coordinates",
            }
            for key, label in field_map.items():
                if val := data.get(key):
                    lines.append(f"  {label:<12}: {val}")
            return SkillResult(success=True, output="\n".join(lines), data=data)
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class DNSLookupSkill(BaseSkill):
    name        = "dns_lookup"
    description = (
        "Resolve DNS records for a domain. "
        "Args: domain (str), record_type (str: 'A'|'AAAA'|'MX'|'TXT'|'NS'|'CNAME', default 'A')."
    )
    platforms   = ["all"]

    async def execute(self, domain: str = "", record_type: str = "A", **kwargs) -> SkillResult:
        if not domain:
            return SkillResult(success=False, output="", error="No domain provided.")
        record_type = record_type.upper()
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    "https://dns.google/resolve",
                    params={"name": domain, "type": record_type},
                )
                resp.raise_for_status()
            data    = resp.json()
            answers = data.get("Answer") or data.get("Authority") or []
            if not answers:
                return SkillResult(
                    success=True,
                    output=f"🌐 No {record_type} records found for `{domain}`.",
                    data={},
                )
            lines = [f"🌐 **DNS {record_type} for `{domain}`**\n"]
            for a in answers:
                ttl  = a.get("TTL", 0)
                data_ = a.get("data", "?")
                lines.append(f"  {data_:<50} TTL: {ttl}s")
            return SkillResult(success=True, output="\n".join(lines), data={"answers": answers})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class PingSkill(BaseSkill):
    name        = "ping"
    description = "Ping a host and measure response time. Args: host (str), count (int, default 4)."
    platforms   = ["all"]

    async def execute(self, host: str = "", count: int = 4, **kwargs) -> SkillResult:
        if not host:
            return SkillResult(success=False, output="", error="No host provided.")
        # Sanitize host
        if not re.match(r'^[\w.\-]+$', host):
            return SkillResult(success=False, output="", error="Invalid host format.")
        count   = max(1, min(10, count))
        rc, out = await _run(f"ping -c {count} -W 3 {host}")
        if rc == 0:
            return SkillResult(
                success=True,
                output=f"📡 **Ping `{host}`**\n```\n{out}\n```",
                data={"host": host, "reachable": True},
            )
        return SkillResult(
            success=True,
            output=f"📡 **Ping `{host}`** — unreachable\n```\n{out[-300:]}\n```",
            data={"host": host, "reachable": False},
        )


class TracerouteSkill(BaseSkill):
    name        = "traceroute"
    description = "Trace the network path to a host. Args: host (str), max_hops (int, default 15)."
    platforms   = ["all"]

    async def execute(self, host: str = "", max_hops: int = 15, **kwargs) -> SkillResult:
        if not host:
            return SkillResult(success=False, output="", error="No host provided.")
        if not re.match(r'^[\w.\-]+$', host):
            return SkillResult(success=False, output="", error="Invalid host format.")
        max_hops = max(5, min(30, max_hops))
        # Try traceroute, fallback to tracepath
        rc, out = await _run(f"traceroute -m {max_hops} -w 2 {host}", timeout=60)
        if rc != 0:
            rc, out = await _run(f"tracepath -m {max_hops} {host}", timeout=60)
        return SkillResult(
            success=True,
            output=f"🗺️ **Traceroute `{host}`**\n```\n{out[:2000]}\n```",
            data={"host": host},
        )
