"""
comms/discord_send.py — Nexara Skills Warehouse
Post messages to Discord via webhooks.

Required env: DISCORD_WEBHOOK_URL
Dependencies: httpx
Platforms   : all
"""

import os
import httpx
from skills.base import BaseSkill, SkillResult

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
TIMEOUT = httpx.Timeout(connect=10, read=15, write=5, pool=5)


class DiscordSendSkill(BaseSkill):
    name        = "discord_send"
    description = (
        "Post a message to a Discord channel via webhook. "
        "Args: message (str), username (str opt), avatar_url (str opt), embed_title (str opt), embed_color (int opt)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        message:     str = "",
        username:    str = "Nexara",
        avatar_url:  str = "",
        embed_title: str = "",
        embed_color: int = 0x7289DA,
        **kwargs,
    ):
        if not message:
            return SkillResult(success=False, output="", error="No message provided.")
        webhook = os.getenv("DISCORD_WEBHOOK_URL", DISCORD_WEBHOOK)
        if not webhook:
            return SkillResult(success=False, output="", error="DISCORD_WEBHOOK_URL not set in .env")

        payload: dict = {"username": username}
        if avatar_url:
            payload["avatar_url"] = avatar_url

        if embed_title:
            payload["embeds"] = [{
                "title":       embed_title,
                "description": message,
                "color":       embed_color,
            }]
        else:
            payload["content"] = message

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(webhook, json=payload)
                if resp.status_code not in (200, 204):
                    resp.raise_for_status()
            return SkillResult(
                success=True,
                output=f"✅ Discord message sent as **{username}**: _{message[:80]}_",
                data={},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
