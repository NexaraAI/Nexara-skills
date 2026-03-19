"""
core/email_send.py — Nexara Skills Warehouse
Send emails via SMTP. Reads credentials from env.

Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
Dependencies     : none (stdlib smtplib)
Platforms        : all
"""

import asyncio
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from skills.base import BaseSkill, SkillResult

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


class EmailSendSkill(BaseSkill):
    name        = "email_send"
    description = (
        "Send an email via SMTP. "
        "Args: to (str), subject (str), body (str), html (bool, default False)."
    )
    platforms   = ["all"]

    async def execute(self, to: str = "", subject: str = "", body: str = "", html: bool = False, **kwargs):
        if not to:
            return SkillResult(success=False, output="", error="No recipient provided.")
        if not SMTP_USER or not SMTP_PASS:
            return SkillResult(success=False, output="", error="SMTP credentials not set. Add SMTP_USER and SMTP_PASS to .env")

        def _send():
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject or "(no subject)"
            msg["From"]    = SMTP_FROM
            msg["To"]      = to
            content_type   = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_FROM, to, msg.as_string())

        try:
            await asyncio.to_thread(_send)
            return SkillResult(
                success=True,
                output=f"✉️ Email sent to **{to}**\nSubject: _{subject}_",
                data={"to": to, "subject": subject},
            )
        except smtplib.SMTPAuthenticationError:
            return SkillResult(success=False, output="", error="SMTP authentication failed. Check SMTP_USER/SMTP_PASS.")
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
