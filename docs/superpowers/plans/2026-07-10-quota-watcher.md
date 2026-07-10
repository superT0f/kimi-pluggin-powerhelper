# Quota Watcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a quota watcher that parses Kimi Code CLI `/usage` output and alerts the user at 70% and every 5% increment thereafter.

**Architecture:** A Python tool `tools/quota.py` handles parsing, threshold logic, and state persistence. A skill and slash command feed `/usage` output into the tool. A `Stop` hook prints a periodic reminder.

**Tech Stack:** Python 3, standard library (json, re, pathlib), plugin manifest hooks.

---

## File map

| File | Responsibility |
|---|---|
| `tools/quota.py` | Parse `/usage`, compute alerts, read/write `.data/quota-alerts.json`, reminder mode. |
| `skills/quota-watch/SKILL.md` | Keyword-triggered skill. |
| `commands/quota.md` | Slash command `/powerhelper:quota`. |
| `kimi.plugin.json` | Declare `sessionStart.skill` and `Stop` hook. |
| `tests/test_quota.py` | Unit tests for parsing and threshold logic. |
| `README.md` | Document the new skill/command. |

---

### Task 1: Implement `tools/quota.py`

**Files:**
- Create: `tools/quota.py`
- Test: `tests/test_quota.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path
from tools.quota import parse_usage, compute_alerts, reminder, ALERT_FILE

USAGE_TEXT = """Daily usage: 14500 / 20000 tokens (72.5%)
Weekly usage: 34000 / 100000 tokens (34.0%)"""


def test_parse_usage_extracts_daily_and_weekly():
    result = parse_usage(USAGE_TEXT)
    assert result["daily"] == {"used": 14500, "total": 20000, "pct": 72.5}
    assert result["weekly"] == {"used": 34000, "total": 100000, "pct": 34.0}


def test_compute_alerts_triggers_at_70():
    state = {}
    result = compute_alerts({"daily": {"used": 14500, "total": 20000, "pct": 72.5}}, state)
    assert "Daily quota at 72.5%" in result
    assert state["daily"]["last_alert_pct"] == 70


def test_compute_alerts_resets_on_lower_usage():
    state = {"daily": {"last_alert_pct": 80, "last_alert_date": "2026-07-09"}}
    result = compute_alerts({"daily": {"used": 1000, "total": 20000, "pct": 5.0}}, state)
    assert state["daily"]["last_alert_pct"] == 0
    assert "reset" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_quota.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement quota.py**

```python
#!/usr/bin/env python3
"""Quota watcher for PowerHelper.

Parses Kimi Code CLI /usage output and alerts on thresholds.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ALERT_FILE = Path(".data") / "quota-alerts.json"
REMINDER_EVERY_N_TURNS = 10
FIRST_ALERT_PCT = 70
TIER_STEP = 5


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_state(path: Path = ALERT_FILE) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict, path: Path = ALERT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_window(state: dict, window: str) -> dict:
    if window not in state:
        state[window] = {
            "last_alert_pct": 0,
            "last_alert_date": "",
            "turn_counter": 0,
        }
    return state[window]


def parse_usage(text: str) -> dict:
    """Extract daily and weekly usage numbers from /usage output."""
    result: dict = {}
    patterns = [
        (r"daily[^\n]*?(?P<used>\d+)\s*/\s*(?P<total>\d+)[^\n]*?\((?P<pct>\d+(?:\.\d+)?)\s*%?\)", "daily"),
        (r"weekly[^\n]*?(?P<used>\d+)\s*/\s*(?P<total>\d+)[^\n]*?\((?P<pct>\d+(?:\.\d+)?)\s*%?\)", "weekly"),
    ]
    for pattern, window in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[window] = {
                "used": int(match.group("used")),
                "total": int(match.group("total")),
                "pct": float(match.group("pct")),
            }
    return result


def tier_for_pct(pct: float) -> int:
    """Return the highest alert tier reached by pct, or 0 if below first alert."""
    if pct < FIRST_ALERT_PCT:
        return 0
    # Tiers: 70, 75, 80, 85, 90, 95, 100
    tier = FIRST_ALERT_PCT
    while tier + TIER_STEP <= 100 and pct >= tier + TIER_STEP:
        tier += TIER_STEP
    return tier


def compute_alerts(usage: dict, state: dict) -> str:
    """Update state and return a human-readable alert message."""
    messages = []
    for window in ("daily", "weekly"):
        data = usage.get(window)
        if not data:
            continue
        win_state = ensure_window(state, window)
        pct = data["pct"]
        tier = tier_for_pct(pct)
        last_tier = win_state.get("last_alert_pct", 0)

        # Detect reset: pct dropped more than 10 points below last tier or used decreased significantly
        if last_tier > 0 and (pct < max(0, last_tier - 15)):
            win_state["last_alert_pct"] = 0
            win_state["last_alert_date"] = ""
            messages.append(f"🔄 {window.capitalize()} quota appears to have reset (now {pct:.1f}%).")
            last_tier = 0

        if tier > 0 and tier > last_tier:
            win_state["last_alert_pct"] = tier
            win_state["last_alert_date"] = today_str()
            messages.append(
                f"⚠️  {window.capitalize()} quota at {pct:.1f}% — threshold {tier}% reached."
            )

    if not messages:
        return "✅ No new quota threshold crossed."
    return "\n".join(messages)


def reminder(state: dict | None = None) -> str:
    """Increment turn counter and return a reminder every N turns."""
    if state is None:
        state = load_state()
    ensure_window(state, "daily")
    ensure_window(state, "weekly")
    state["daily"]["turn_counter"] += 1
    state["weekly"]["turn_counter"] += 1
    daily_count = state["daily"]["turn_counter"]
    weekly_count = state["weekly"]["turn_counter"]
    save_state(state)
    if daily_count % REMINDER_EVERY_N_TURNS == 0 or weekly_count % REMINDER_EVERY_N_TURNS == 0:
        return "💡 Tip: run /usage and say 'quota' to check your daily/weekly token usage."
    return ""


def session_check(state: dict | None = None) -> str:
    """On session start, remind if last alert was >= 70%."""
    if state is None:
        state = load_state()
    messages = []
    for window in ("daily", "weekly"):
        win_state = state.get(window, {})
        last_tier = win_state.get("last_alert_pct", 0)
        if last_tier >= FIRST_ALERT_PCT:
            messages.append(
                f"⚠️  Last {window} quota alert was {last_tier}%. "
                "Run /usage and say 'quota' to check the current level."
            )
    if messages:
        return "\n".join(messages)
    return ""


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: quota.py <check|remind|session>")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "check":
        text = " ".join(args)
        if not text or text == "":
            print("Please paste the output of /usage after the command.")
            return 0
        usage = parse_usage(text)
        if not usage:
            print("Could not parse /usage output.")
            print("Expected something like: 'Daily usage: 12345 / 20000 tokens (61.7%)'")
            return 0
        state = load_state()
        result = compute_alerts(usage, state)
        save_state(state)
        print(result)
    elif command == "remind":
        msg = reminder()
        if msg:
            print(msg)
    elif command == "session":
        msg = session_check()
        if msg:
            print(msg)
    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest tests/test_quota.py -v
```

Expected: PASS.

- [ ] **Step 5: Manual CLI check**

```bash
python3 tools/quota.py check "Daily usage: 14500 / 20000 tokens (72.5%)"
```

Expected: alert message.

```bash
python3 tools/quota.py remind
```

Expected: reminder message every 10th call.

- [ ] **Step 6: Commit**

```bash
git add tools/quota.py tests/test_quota.py
git commit -m "feat: add quota watcher tool and tests"
```

---

### Task 2: Add slash command

**Files:**
- Create: `commands/quota.md`

- [ ] **Step 1: Write quota.md**

```markdown
---
description: Check token quota against alert thresholds
---

You are the PowerHelper Quota Watcher.

All output must be in English.

If the user has provided `/usage` output as arguments, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/quota.py" check "$ARGUMENTS"
```

If no arguments are given, ask the user politely to run `/usage` and paste the output.

Print the raw script output without modification. Do not add extra commentary.
```

- [ ] **Step 2: Commit**

```bash
git add commands/quota.md
git commit -m "feat: add /powerhelper:quota slash command"
```

---

### Task 3: Add skill

**Files:**
- Create: `skills/quota-watch/SKILL.md`

- [ ] **Step 1: Create directory and skill file**

```bash
mkdir -p skills/quota-watch
```

```markdown
---
name: quota-watch
description: Monitor token quota and alert on thresholds
type: prompt
whenToUse: When the user says quota, usage, or daily check
---

You are the PowerHelper Quota Watcher.

All output must be in English.

## User-provided /usage output

If the user pasted `/usage` output, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/quota.py" check "$ARGUMENTS"
```

Print the raw output without modification.

## No data

If the user only said a keyword like "quota" or "usage" without pasting output, ask them:

> Please run `/usage` in Kimi Code CLI and paste the output here.

Do not add extra commentary beyond the script output or the polite request.
```

- [ ] **Step 2: Commit**

```bash
git add skills/quota-watch/SKILL.md
git commit -m "feat: add quota-watch skill"
```

---

### Task 4: Update session-start skill and manifest

**Files:**
- Modify: `skills/using-powerhelper/SKILL.md`
- Modify: `kimi.plugin.json`

- [ ] **Step 1: Read current session-start skill**

```bash
cat skills/using-powerhelper/SKILL.md
```

- [ ] **Step 2: Add quota check to session-start skill**

Append to `skills/using-powerhelper/SKILL.md`:

```markdown
## Quota check on session start

At the start of every session, run:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/quota.py" session
```

Print the raw output without modification. If there is no output, say nothing.
```

- [ ] **Step 3: Add Stop hook to manifest**

Edit `kimi.plugin.json` to add the `hooks` array:

```json
{
  "name": "powerhelper",
  "version": "0.1.0",
  "description": "A hello-world plugin to learn Kimi Code custom plugins",
  "skills": "./skills/",
  "sessionStart": {
    "skill": "using-powerhelper"
  },
  "commands": "./commands/",
  "hooks": [
    {
      "event": "Stop",
      "command": "python3 ./tools/quota.py remind",
      "timeout": 5
    }
  ],
  "interface": {
    "displayName": "PowerHelper",
    "shortDescription": "Hello-world plugin for learning Kimi Code plugins"
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add skills/using-powerhelper/SKILL.md kimi.plugin.json
git commit -m "feat: add quota session check and Stop hook"
```

---

### Task 5: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add quota watcher section**

After the Dungeon Arena section, add:

```markdown
## Quota Watcher

Monitor your Kimi Code CLI token quota and get alerted when you cross 70%, then every 5%.

### Usage

Run in Kimi Code CLI:

```text
/usage
```

Then paste the output:

```text
/powerhelper:quota Daily usage: 14500 / 20000 tokens (72.5%)
```

Or simply say:

```text
quota
```

The assistant will ask for your `/usage` output and alert you if a new threshold is reached.

Quota alert history is stored in `.data/quota-alerts.json`.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document Quota Watcher"
```

---

### Task 6: Validate and push

- [ ] **Step 1: Run all tests**

```bash
python3 -m py_compile tools/quota.py tools/dungeon/*.py tools/hi-there.py
python3 -m pytest tests/test_quota.py tests/test_progression.py -v
```

Expected: all PASS.

- [ ] **Step 2: Verify manifest syntax**

```bash
python3 -c "import json; json.load(open('kimi.plugin.json'))"
```

Expected: no error.

- [ ] **Step 3: Push**

```bash
git push origin main
```

---

## Spec coverage check

| Spec requirement | Task |
|---|---|
| Parse `/usage` output | Task 1 |
| Threshold logic 70% + 5% tiers | Task 1 |
| Alert state persistence | Task 1 |
| Slash command | Task 2 |
| Keyword skill | Task 3 |
| Session start check | Task 4 |
| Stop hook reminder every 10 turns | Task 4 |
| README documentation | Task 5 |
| Tests | Task 1 |

## Placeholder scan

No TBD, TODO, or vague steps. Each step includes concrete code or commands.
