"""
core/password_gen.py — Nexara Skills Warehouse
Generate cryptographically secure passwords and passphrases.

Dependencies: none (stdlib secrets)
Platforms   : all
"""

import secrets
import string
from skills.base import BaseSkill, SkillResult

WORDLIST_URL = "https://raw.githubusercontent.com/EFF/BIP39-en/master/BIP39-en.txt"


class PasswordGenSkill(BaseSkill):
    name        = "password_gen"
    description = (
        "Generate a secure password or passphrase. "
        "Args: length (int, default 20), count (int, default 1), "
        "include_symbols (bool, default True), passphrase (bool, default False), words (int, default 4)."
    )
    platforms   = ["all"]

    async def execute(
        self,
        length:           int  = 20,
        count:            int  = 1,
        include_symbols:  bool = True,
        passphrase:       bool = False,
        words:            int  = 4,
        **kwargs,
    ):
        count  = max(1, min(10, count))
        length = max(8, min(128, length))

        if passphrase:
            # Simple passphrase from built-in word pool
            import hashlib
            word_pool = [
                "apple","brave","cloud","dance","eagle","flame","grace","hero",
                "ivory","jewel","knife","lemon","magic","night","ocean","pearl",
                "queen","raven","storm","tiger","ultra","vivid","water","xenon",
                "yacht","zebra","amber","blaze","crisp","delta","ember","frost",
                "gloom","haven","indie","joker","karma","lunar","maple","noble",
            ]
            results = []
            for _ in range(count):
                chosen     = [secrets.choice(word_pool) for _ in range(max(3, words))]
                separator  = secrets.choice(["-", "_", ".", "!"])
                num        = secrets.randbelow(100)
                passphrase_str = separator.join(chosen) + str(num)
                results.append(passphrase_str)
            output = "🔐 **Passphrases:**\n" + "\n".join(f"  `{r}`" for r in results)
            return SkillResult(success=True, output=output, data={"passwords": results})

        charset = string.ascii_letters + string.digits
        if include_symbols:
            charset += "!@#$%^&*()-_=+[]{}|;:,.<>?"

        results = []
        for _ in range(count):
            pwd = "".join(secrets.choice(charset) for _ in range(length))
            results.append(pwd)

        output = f"🔐 **Password(s)** (len={length}, symbols={include_symbols}):\n"
        output += "\n".join(f"  `{r}`" for r in results)
        return SkillResult(success=True, output=output, data={"passwords": results})
