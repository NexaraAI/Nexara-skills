# Contributing to nexara-skills

Thanks for contributing. This guide is short and direct.

---

## Quick start

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/nexara-skills
cd nexara-skills

# 2. Create a branch
git checkout -b add-my-skill

# 3. Copy the template
cp skill_template.py core/my_skill.py   # or android/, linux/, etc.

# 4. Implement your skill

# 5. Run local checks
python3 .github/scripts/ast_scan.py
python3 .github/scripts/interface_check.py
python3 .github/scripts/test_imports.py

# 6. Open a PR
```

---

## What makes a good skill

**Useful** — Does something the agent couldn't do with existing skills.

**Correct platform tag** — If it only works on Android, say so. Sending Android skill schemas to a Linux agent wastes ~50 tokens per request.

**Handles errors** — Every failure path returns `SkillResult(success=False, error="...")`. Never raise uncaught exceptions — they break the agent's ReAct loop.

**Non-blocking** — Use `asyncio.to_thread()` for CPU-heavy work. Use `asyncio.create_subprocess_shell` for shell commands. Never use `subprocess.run()` or `os.system()`.

**Minimal dependencies** — Prefer stdlib. If you need a package, check it's already in Nexara's `requirements.txt`. If it isn't, mention it in your PR.

---

## File naming

```
your_feature.py          # filename stem = skill name
```

The skill `name` attribute must match the filename stem exactly:
```python
# File: core/my_awesome_skill.py
class MyAwesomeSkill(BaseSkill):
    name = "my_awesome_skill"   # must match
```

One file can contain multiple skill classes if they're closely related (e.g. `sms.py` has `ReadSMSSkill`, `SendSMSSkill`, `ReadContactsSkill`).

---

## PR checklist

Before submitting:

- [ ] Skill is in the right category folder (`core/`, `android/`, `linux/`, `windows/`, `macos/`)
- [ ] `name` matches filename stem
- [ ] `description` is clear and mentions key args
- [ ] `platforms` list is accurate
- [ ] `execute()` is `async` and accepts `**kwargs`
- [ ] All error paths return `SkillResult(success=False, error="...")`
- [ ] No `eval`, `exec`, `os.system`, `subprocess.run`, or `ctypes`
- [ ] All three local CI scripts pass

---

## What CI checks

On every PR against `main`:

| Check | What it does |
|---|---|
| `ast_scan.py` | Blocks dangerous patterns |
| `interface_check.py` | Verifies BaseSkill compliance |
| `manifest_check.py` | Validates manifest.json integrity |
| `test_imports.py` | Smoke-tests every import |

On merge to `main`:
- `regenerate_manifest.py` recomputes checksums and updates `manifest.json` automatically

---

## Questions

Open an issue or discussion on GitHub.
