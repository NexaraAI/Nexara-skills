"""
core/system_info.py — Nexara Skills Warehouse
System introspection: CPU, RAM, disk, processes, network, self-heal.

Dependencies: psutil (optional, falls back to shell)
Platforms   : all
"""

import asyncio
import time
from pathlib import Path

from skills.base import BaseSkill, SkillResult


async def _run(cmd: str, timeout: int = 15) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, out.decode("utf-8", errors="replace").strip()


class SystemInfoSkill(BaseSkill):
    name        = "system_info"
    description = "Full system snapshot: CPU, RAM, disk, network, uptime."
    platforms   = ["all"]

    async def execute(self, **kwargs) -> SkillResult:
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage(str(Path.home()))
            net  = psutil.net_io_counters()
            up   = time.time() - psutil.boot_time()
            h, r = divmod(int(up), 3600)
            m, s = divmod(r, 60)
            def mb(b): return f"{b/1_048_576:.1f} MB"
            def gb(b): return f"{b/1_073_741_824:.1f} GB"
            output = (
                f"🖥️ **System Info**\n\n"
                f"⚙️  CPU    : {cpu:.1f}%\n"
                f"🧠 RAM    : {mb(ram.used)} / {mb(ram.total)}  ({ram.percent}%)\n"
                f"💾 Disk   : {gb(disk.used)} / {gb(disk.total)}  ({disk.percent}%)\n"
                f"📡 Net    : ↑ {mb(net.bytes_sent)}  ↓ {mb(net.bytes_recv)}\n"
                f"⏱️  Uptime : {h}h {m}m {s}s"
            )
            return SkillResult(
                success=True, output=output,
                data={"cpu": cpu, "ram_pct": ram.percent, "disk_pct": disk.percent},
            )
        except ImportError:
            _, uname = await _run("uname -a")
            _, mem   = await _run("free -h")
            _, dsk   = await _run("df -h ~")
            return SkillResult(success=True, output=f"```\n{uname}\n\n{mem}\n\n{dsk}\n```", data={})


class ProcessListSkill(BaseSkill):
    name        = "process_list"
    description = "List running processes sorted by CPU or memory. Args: sort_by, limit."
    platforms   = ["all"]

    async def execute(self, sort_by: str = "cpu", limit: int = 15, **kwargs) -> SkillResult:
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
                try: procs.append(p.info)
                except Exception: pass

            key   = "memory_info" if sort_by == "mem" else "cpu_percent"
            procs = sorted(
                procs,
                key=lambda x: (x.get("memory_info").rss if x.get("memory_info") else 0)
                              if sort_by == "mem" else (x.get("cpu_percent") or 0),
                reverse=True
            )[:limit]

            lines = [f"🔄 **Top {limit} Processes (by {sort_by})**\n"]
            lines.append(f"{'PID':<8} {'NAME':<25} {'CPU%':>6} {'MEM MB':>8}  STATUS")
            lines.append("─" * 56)
            for p in procs:
                mem_mb = p["memory_info"].rss / 1_048_576 if p.get("memory_info") else 0
                lines.append(
                    f"{p['pid']:<8} {(p['name'] or '?')[:24]:<25} "
                    f"{p.get('cpu_percent', 0):>6.1f} {mem_mb:>8.1f}  {p.get('status', '?')}"
                )
            return SkillResult(success=True, output="```\n" + "\n".join(lines) + "\n```", data={})
        except ImportError:
            _, out = await _run(f"ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -{limit+1}")
            return SkillResult(success=True, output=f"```\n{out}\n```", data={})


class KillProcessSkill(BaseSkill):
    name        = "kill_process"
    description = "Kill a process by PID or name. Args: pid (int) OR name (str), signal."
    platforms   = ["all"]

    async def execute(self, pid: int = 0, name: str = "", signal: str = "TERM", **kwargs) -> SkillResult:
        if pid:
            rc, out = await _run(f"kill -{signal} {pid}")
        elif name:
            rc, out = await _run(f"pkill -{signal} -f '{name}'")
        else:
            return SkillResult(success=False, output="", error="Provide pid or name.")
        if rc == 0:
            target = f"PID {pid}" if pid else f"`{name}`"
            return SkillResult(success=True, output=f"🔫 Sent {signal} to {target}.", data={})
        return SkillResult(success=False, output="", error=out)


class NetworkScanSkill(BaseSkill):
    name        = "network_scan"
    description = "Scan open ports on a host. Args: target, ports (comma-separated)."
    platforms   = ["all"]

    async def execute(self, target: str = "localhost", ports: str = "22,80,443,8080", **kwargs) -> SkillResult:
        results = []
        for port in [p.strip() for p in ports.split(",")]:
            rc, _  = await _run(f"nc -z -w 2 {target} {port}")
            icon   = "🟢 OPEN" if rc == 0 else "🔴 closed"
            results.append(f"  Port {port:>5} : {icon}")
        return SkillResult(
            success=True,
            output=f"🔍 **Port Scan** — `{target}`\n\n" + "\n".join(results),
            data={},
        )


class SelfHealSkill(BaseSkill):
    name        = "self_heal"
    description = "Fix common issues. Args: action ('restart_bot'|'clear_cache'|'upgrade_deps')."
    platforms   = ["all"]

    async def execute(self, action: str = "restart_bot", **kwargs) -> SkillResult:
        if action == "clear_cache":
            await _run("pip cache purge")
            await _run("find ~/.nexara -name '*.log' -size +10M -delete")
            await _run("find ~ -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null")
            return SkillResult(success=True, output="🧹 Cache cleared.", data={})

        if action == "upgrade_deps":
            rc, out = await _run("pip install -q -r requirements.txt --upgrade", timeout=120)
            return SkillResult(
                success=rc == 0,
                output="✅ Dependencies upgraded." if rc == 0 else out[:500],
                data={},
                error="" if rc == 0 else out[:500],
            )

        if action == "restart_bot":
            import subprocess
            script = Path(__file__).parents[1] / "update.sh"
            if script.exists():
                subprocess.Popen(
                    ["bash", str(script)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                )
                return SkillResult(success=True, output="🔄 Restart initiated.", data={})
            return SkillResult(success=False, output="", error="update.sh not found.")

        return SkillResult(success=False, output="", error=f"Unknown action: {action}")
