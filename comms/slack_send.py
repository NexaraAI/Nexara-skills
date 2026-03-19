"""
comms/slack_send.py — Nexara Skills Warehouse
Post messages to Slack via Incoming Webhooks.

Required env: SLACK_WEBHOOK_URL
Dependencies: httpx
Platforms   : all
"""

import os
import httpx
from skills.base import BaseSkill, SkillResult

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
TIMEOUT = httpx.Timeout(connect=10, read=15, write=5, pool=5)


class SlackSendSkill(BaseSkill):
    name        = "slack_send"
    description = (
        "Post a message to a Slack channel via webhook. "
        "Args: message (str), username (str opt), emoji (str opt), channel (str opt)."
    )
    platforms   = ["all"]

    async def execute(self, message: str = "", username: str = "Nexara", emoji: str = ":robot_face:", channel: str = "", **kwargs):
        if not message:
            return SkillResult(success=False, output="", error="No message provided.")
        webhook = os.getenv("SLACK_WEBHOOK_URL", SLACK_WEBHOOK)
        if not webhook:
            return SkillResult(success=False, output="", error="SLACK_WEBHOOK_URL not set in .env")
        payload = {"text": message, "username": username, "icon_emoji": emoji}
        if channel:
            payload["channel"] = channel
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.post(webhook, json=payload)
                resp.raise_for_status()
            return SkillResult(
                success=True,
                output=f"✅ Slack message sent to {channel or 'default channel'}: _{message[:80]}_",
                data={"channel": channel},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
