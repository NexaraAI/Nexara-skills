# nexara-skills

**Official skill warehouse for [Nexara Agent V1](https://github.com/nexara-agent/nexara)**

Skills are Python modules fetched by the Nexara agent at startup — only skills matching the detected platform are loaded. No Android skills on Linux. No Linux skills on Android. Token-efficient by design.

---

## Skill Categories

| Category  | Platform       | Skills |
|-----------|---------------|--------|
| `core`    | All platforms  | web_search, web_scrape, download, file_ops, code_exec, system_info, command |
| `android` | Termux/Android | battery, camera, sms, device_control |
| `linux`   | Linux/Codespace/WSL/Docker | apt_manage, systemd, docker_ops, ssh_exec |
| `windows` | Windows native | powershell |
| `macos`   | macOS          | brew, applescript |

---

## Adding a Skill

1. **Fork** this repository
2. **Copy** `skill_template.py` into the right category folder
3. **Rename** it: `your_skill_name.py`
4. **Implement** your skill — follow the template's checklist
5. **Test** it locally: `python3 .github/scripts/test_imports.py`
6. **Open a PR** — CI will automatically:
   - Run an AST safety scan
   - Check interface compliance
   - Validate manifest integrity
   - Test all imports
7. On merge, the manifest and checksums are auto-regenerated

### Skill file structure

```python
from skills.base import BaseSkill, SkillResult

class YourSkillNameSkill(BaseSkill):
    name        = "your_skill_name"     # must match filename stem
    description = "What it does."      # shown to the LLM
    platforms   = ["all"]              # or ["android"], ["linux"], etc.

    async def execute(self, arg: str = "", **kwargs) -> SkillResult:
        # ... your logic ...
        return SkillResult(success=True, output="Result text", data={})
```

### Platform tags

| Tag       | Loads on                          |
|-----------|-----------------------------------|
| `all`     | Every platform                    |
| `android` | Termux/Android only               |
| `linux`   | Linux, Codespace, WSL, Docker     |
| `windows` | Windows native                    |
| `macos`   | macOS only                        |

---

## manifest.json

The agent fetches `manifest.json` to know what skills are available and at what versions. Each entry:

```json
{
  "category":    "core",
  "version":     "1.0.0",
  "file":        "core/web_search.py",
  "checksum":    "sha256:abc123...",
  "platforms":   ["all"],
  "description": "DuckDuckGo web search",
  "min_agent":   "1.0.0"
}
```

Checksums are verified before loading. A tampered file will be rejected.

---

## Release Channels

| Channel  | Description                              |
|----------|------------------------------------------|
| `stable` | Reviewed and tested — default            |
| `beta`   | New skills, may have rough edges         |
| `dev`    | Unreviewed PRs — for testing only        |

Set your channel in `.env`: `SKILL_CHANNEL=stable`

---

## Rules for Contributors

- No `eval()`, `exec()`, `__import__()`, `os.system()`, or `ctypes`
- No hardcoded paths — use `Path.home()` or config values
- No blocking I/O — use `asyncio.to_thread()` for heavy work
- Every external command goes through `asyncio.create_subprocess_shell`
- Always accept `**kwargs` in `execute()` for forward compatibility
- Return `SkillResult(success=False, error="...")` on failure — never raise uncaught exceptions
- Declare `platforms` accurately — wrong tags waste the agent's token budget
- One skill file per logical feature group (e.g. `sms.py` has read, send, contacts)

---

## Local Testing

```bash
# Clone the repo
git clone https://github.com/nexara-agent/nexara-skills
cd nexara-skills

# Run all CI checks locally
python3 .github/scripts/ast_scan.py
python3 .github/scripts/interface_check.py
python3 .github/scripts/manifest_check.py
python3 .github/scripts/test_imports.py
```

---

## ⚖️ License

Nexara is open-source software licensed under the **Apache License 2.0**. 
See the `LICENSE` file for more details.

