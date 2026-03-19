"""
comms/ntfy_send.py — Nexara Skills Warehouse
Push notifications via ntfy.sh (free, no account needed).

Dependencies: httpx
Platforms   : all
"""

import httpx
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=15, write=5, pool=5)


class NtfySendSkill(BaseSkill):
    name        = "ntfy_send"
    description = (
        "Send a push notification via ntfy.sh (free). "
        "Args: topic (str — your unique topic name), message (str), "
        "title (str opt), priority ('min'|'low'|'default'|'high'|'urgent'), "
        "tags (list opt)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        topic:    str   = "",
        message:  str   = "",
        title:    str   = "Nexara",
        priority: str   = "default",
        tags:     list  = None,
        **kwargs,
    ):
        if not topic or not message:
            return SkillResult(success=False, output="", error="topic and message are required.")
        headers = {
            "Title":    title,
            "Priority": priority,
        }
        if tags:
            headers["Tags"] = ",".join(tags)
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(
                    f"https://ntfy.sh/{topic}",
                    content=message.encode(),
                    headers=headers,
                )
                resp.raise_for_status()
            return SkillResult(
                success=True,
                output=(
                    f"🔔 **ntfy.sh notification sent**\n"
                    f"Topic    : `{topic}`\n"
                    f"Title    : {title}\n"
                    f"Message  : {message[:80]}\n"
                    f"Subscribe: `ntfy subscribe {topic}` or https://ntfy.sh/{topic}"
                ),
                data={"topic": topic},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
