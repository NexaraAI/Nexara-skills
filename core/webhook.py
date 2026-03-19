"""
core/webhook.py — Nexara Skills Warehouse
Send HTTP webhooks (POST/GET/PUT) to any URL.

Dependencies: httpx
Platforms   : all
"""

import json as _json
import httpx
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=5)


class WebhookSkill(BaseSkill):
    name        = "webhook"
    description = (
        "Send an HTTP request (webhook) to any URL. "
        "Args: url (str), method ('POST'|'GET'|'PUT'|'DELETE'), "
        "payload (dict opt), headers (dict opt)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        url:     str  = "",
        method:  str  = "POST",
        payload: dict = None,
        headers: dict = None,
        **kwargs,
    ):
        if not url:
            return SkillResult(success=False, output="", error="No URL provided.")
        method  = method.upper()
        payload = payload or {}
        headers = headers or {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                if method == "GET":
                    resp = await client.get(url, params=payload, headers=headers)
                elif method == "POST":
                    resp = await client.post(url, json=payload, headers=headers)
                elif method == "PUT":
                    resp = await client.put(url, json=payload, headers=headers)
                elif method == "DELETE":
                    resp = await client.delete(url, headers=headers)
                else:
                    return SkillResult(success=False, output="", error=f"Unsupported method: {method}")

            ok = resp.status_code < 400
            try:
                body = resp.json()
                body_str = _json.dumps(body, indent=2)[:500]
            except Exception:
                body_str = resp.text[:500]

            return SkillResult(
                success=ok,
                output=(
                    f"🔔 **Webhook {method}** → `{url}`\n"
                    f"Status: `{resp.status_code}`\n"
                    f"Response:\n```\n{body_str}\n```"
                ),
                data={"status_code": resp.status_code, "ok": ok},
                error="" if ok else f"HTTP {resp.status_code}",
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
