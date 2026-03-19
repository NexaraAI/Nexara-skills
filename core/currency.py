"""
core/currency.py — Nexara Skills Warehouse
Currency conversion via exchangerate.host (free, no key).

Dependencies: httpx
Platforms   : all
"""

import httpx
from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(connect=10, read=15, write=5, pool=5)


class CurrencySkill(BaseSkill):
    name        = "currency"
    description = (
        "Convert between currencies or get exchange rates. "
        "Args: amount (float), from_currency (str, e.g. 'USD'), to_currency (str, e.g. 'EUR'), "
        "list_rates (bool, default False)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        amount:        float = 1.0,
        from_currency: str   = "USD",
        to_currency:   str   = "EUR",
        list_rates:    bool  = False,
        **kwargs,
    ):
        frm = from_currency.upper()
        to  = to_currency.upper()
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                if list_rates:
                    resp = await client.get(f"https://open.er-api.com/v6/latest/{frm}")
                else:
                    resp = await client.get(f"https://open.er-api.com/v6/latest/{frm}")
                resp.raise_for_status()
            data  = resp.json()
            rates = data.get("rates", {})
            if list_rates:
                top = sorted(
                    [(k, v) for k, v in rates.items()],
                    key=lambda x: x[0]
                )[:30]
                lines = [f"💱 **Exchange Rates (base: {frm})**\n"]
                for k, v in top:
                    lines.append(f"  {k}: {v:.4f}")
                return SkillResult(success=True, output="\n".join(lines), data={"rates": dict(top)})
            if to not in rates:
                return SkillResult(success=False, output="", error=f"Unknown currency: {to}")
            rate       = rates[to]
            converted  = amount * rate
            return SkillResult(
                success=True,
                output=f"💱 **{amount:,.2f} {frm}** = **{converted:,.4f} {to}**\n_Rate: 1 {frm} = {rate:.4f} {to}_",
                data={"amount": amount, "from": frm, "to": to, "rate": rate, "result": converted},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
