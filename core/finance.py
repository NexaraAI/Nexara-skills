"""
core/finance.py — Nexara Skills Warehouse
Stock prices, cryptocurrency prices, and currency conversion.
Uses free public APIs — no API keys required.

Dependencies: httpx
Platforms   : all
"""

import httpx

from skills.base import BaseSkill, SkillResult

TIMEOUT = httpx.Timeout(10, read=20, write=10, pool=10)


class StockPriceSkill(BaseSkill):
    name        = "stock_price"
    description = (
        "Get current stock price and basic info for a ticker symbol. "
        "Args: symbol (str, e.g. 'AAPL', 'TSLA', 'GOOGL')."
    )
    platforms   = ["all"]

    async def execute(self, symbol: str = "", **kwargs) -> SkillResult:
        if not symbol:
            return SkillResult(success=False, output="", error="No ticker symbol provided.")
        symbol = symbol.upper().strip()
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"}) as client:
                resp = await client.get(url, params={"interval": "1d", "range": "5d"})
                resp.raise_for_status()
            data   = resp.json()
            meta   = data["chart"]["result"][0]["meta"]
            price  = meta.get("regularMarketPrice", 0)
            prev   = meta.get("previousClose",      0)
            high   = meta.get("regularMarketDayHigh", 0)
            low    = meta.get("regularMarketDayLow",  0)
            volume = meta.get("regularMarketVolume",  0)
            name   = meta.get("shortName", symbol)
            curr   = meta.get("currency", "USD")
            change    = price - prev
            change_pct = (change / prev * 100) if prev else 0
            arrow  = "📈" if change >= 0 else "📉"

            return SkillResult(
                success=True,
                output=(
                    f"{arrow} **{name}** (`{symbol}`)\n"
                    f"  Price  : **{price:.2f} {curr}**\n"
                    f"  Change : {change:+.2f} ({change_pct:+.2f}%)\n"
                    f"  Range  : {low:.2f} — {high:.2f}\n"
                    f"  Volume : {volume:,}"
                ),
                data={"symbol": symbol, "price": price, "change": change},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=f"Could not fetch `{symbol}`: {exc}")


class CryptoPriceSkill(BaseSkill):
    name        = "crypto_price"
    description = (
        "Get current cryptocurrency price and 24h stats. "
        "Args: coin (str, e.g. 'bitcoin', 'ethereum', 'solana'), currency (str, default 'usd')."
    )
    platforms   = ["all"]

    async def execute(self, coin: str = "", currency: str = "usd", **kwargs) -> SkillResult:
        if not coin:
            return SkillResult(success=False, output="", error="No coin provided.")
        coin     = coin.lower().strip()
        currency = currency.lower().strip()
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(url, params={
                    "vs_currency": currency,
                    "ids": coin,
                    "price_change_percentage": "24h",
                })
                resp.raise_for_status()
            results = resp.json()
            if not results:
                return SkillResult(success=False, output="", error=f"Coin not found: `{coin}`")
            c      = results[0]
            price  = c["current_price"]
            chg    = c["price_change_percentage_24h"] or 0
            high   = c["high_24h"]
            low    = c["low_24h"]
            cap    = c["market_cap"]
            rank   = c["market_cap_rank"]
            arrow  = "📈" if chg >= 0 else "📉"
            def fmt(n): return f"{n:,.2f}" if n < 1000 else f"{n:,.0f}"
            return SkillResult(
                success=True,
                output=(
                    f"{arrow} **{c['name']}** (`{c['symbol'].upper()}`)\n"
                    f"  Price    : **{fmt(price)} {currency.upper()}**\n"
                    f"  24h      : {chg:+.2f}%\n"
                    f"  24h High : {fmt(high)}\n"
                    f"  24h Low  : {fmt(low)}\n"
                    f"  Mkt Cap  : ${cap:,.0f}  (rank #{rank})"
                ),
                data={"coin": coin, "price": price, "change_24h": chg},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))


class CurrencyConvertSkill(BaseSkill):
    name        = "currency_convert"
    description = (
        "Convert an amount between currencies. "
        "Args: amount (float), from_currency (str), to_currency (str)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        amount:        float = 1.0,
        from_currency: str   = "USD",
        to_currency:   str   = "EUR",
        **kwargs,
    ) -> SkillResult:
        frm = from_currency.upper()
        to  = to_currency.upper()
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(
                    f"https://open.er-api.com/v6/latest/{frm}"
                )
                resp.raise_for_status()
            data = resp.json()
            if data.get("result") != "success":
                return SkillResult(success=False, output="", error=f"Could not fetch rates for `{frm}`")
            rates = data.get("rates", {})
            if to not in rates:
                return SkillResult(success=False, output="", error=f"Unknown currency `{to}`")
            rate       = rates[to]
            converted  = amount * rate
            return SkillResult(
                success=True,
                output=(
                    f"💱 **Currency Conversion**\n"
                    f"  {amount:,.2f} {frm} = **{converted:,.4f} {to}**\n"
                    f"  Rate: 1 {frm} = {rate:.6f} {to}"
                ),
                data={"from": frm, "to": to, "rate": rate, "result": converted},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))
