"""
core/timezone.py — Nexara Skills Warehouse
World clock, timezone lookup and conversion (stdlib only).

Dependencies: none (stdlib zoneinfo / pytz fallback)
Platforms   : all
"""

from datetime import datetime
from skills.base import BaseSkill, SkillResult

COMMON_ZONES = {
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "moscow": "Europe/Moscow",
    "dubai": "Asia/Dubai",
    "india": "Asia/Kolkata",
    "kolkata": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "utc": "UTC",
}


def _get_tz(name: str):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        try:
            import pytz
            return pytz.timezone(name)
        except Exception:
            return None


class TimezoneSkill(BaseSkill):
    name        = "timezone"
    description = (
        "Get current time in any timezone or convert between timezones. "
        "Args: location (str), convert_to (str opt), time_str (str opt, e.g. '14:30')."
    )
    platforms   = ["all"]

    async def execute(
        self,
        location:   str = "UTC",
        convert_to: str = "",
        time_str:   str = "",
        **kwargs,
    ):
        zone_name = COMMON_ZONES.get(location.lower(), location)
        tz        = _get_tz(zone_name)
        if not tz:
            return SkillResult(success=False, output="", error=f"Unknown timezone: '{location}'")

        now = datetime.now(tz)
        fmt = "%A, %B %d %Y  %H:%M:%S %Z (UTC%z)"
        lines = [f"🕐 **{location}**\n  {now.strftime(fmt)}"]

        if convert_to:
            to_name = COMMON_ZONES.get(convert_to.lower(), convert_to)
            tz2     = _get_tz(to_name)
            if tz2:
                now2 = now.astimezone(tz2)
                lines.append(f"\n🕐 **{convert_to}**\n  {now2.strftime(fmt)}")
            else:
                lines.append(f"\n⚠️ Unknown destination timezone: '{convert_to}'")

        return SkillResult(success=True, output="\n".join(lines), data={"time": now.isoformat()})
