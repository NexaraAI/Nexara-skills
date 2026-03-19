"""
core/weather.py — Nexara Skills Warehouse
Current weather and forecasts via wttr.in (free, no API key).

Dependencies: httpx
Platforms   : all
"""

import httpx
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=20, write=5, pool=5)


class WeatherSkill(BaseSkill):
    name        = "weather"
    description = (
        "Get current weather and forecast for any city. "
        "Args: location (str), days (1-3), units ('metric'|'imperial')."
    )
    platforms   = ["all"]

    async def execute(self, location: str = "", days: int = 1, units: str = "metric", **kwargs):
        if not location:
            return SkillResult(success=False, output="", error="No location provided.")
        days    = max(1, min(3, days))
        unit_ch = "u" if units == "imperial" else "m"
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    f"https://wttr.in/{location}?format=j1&{unit_ch}",
                    headers={"User-Agent": "Nexara/1.0"},
                )
                resp.raise_for_status()
            data    = resp.json()
            current = data["current_condition"][0]
            area    = data["nearest_area"][0]
            city    = area["areaName"][0]["value"]
            country = area["country"][0]["value"]
            deg     = "°F" if units == "imperial" else "°C"
            temp    = current["temp_F"] if units == "imperial" else current["temp_C"]
            feels   = current["FeelsLikeF"] if units == "imperial" else current["FeelsLikeC"]
            desc    = current["weatherDesc"][0]["value"]
            lines   = [
                f"🌤️ **Weather — {city}, {country}**\n",
                f"  🌡️  Temp     : {temp}{deg}  (feels {feels}{deg})",
                f"  ☁️  Condition: {desc}",
                f"  💧 Humidity : {current['humidity']}%",
                f"  🌬️  Wind     : {current['windspeedKmph']} km/h",
                f"  👁️  Visibility: {current['visibility']} km",
            ]
            for i, day in enumerate(data["weather"][:days], 1):
                hi    = day["maxtempF"] if units == "imperial" else day["maxtempC"]
                lo    = day["mintempF"] if units == "imperial" else day["mintempC"]
                fdesc = day["hourly"][4]["weatherDesc"][0]["value"]
                lines.append(f"\n  📅 Day {i} ({day['date']}): {lo}{deg}–{hi}{deg}  {fdesc}")
            return SkillResult(success=True, output="\n".join(lines), data={"temp": temp, "desc": desc})
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
