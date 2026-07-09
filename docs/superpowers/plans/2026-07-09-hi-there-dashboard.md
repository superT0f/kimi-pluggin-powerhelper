# hi-there Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `hi-there` Skill and slash command to the PowerHelper plugin that displays a daily terminal dashboard (ASCII meme, weather, news) with a 24-hour local cache.

**Architecture:** A Python 3 script (`tools/hi-there.py`) handles caching, network calls, parsing, and formatting. A `SKILL.md` and slash command invoke the script via Bash. Only standard-library Python modules are used.

**Tech Stack:** Markdown, JSON, Python 3 standard library.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `tools/hi-there.py` | Python script: cache management, weather fetch, RSS news fetch, ASCII meme selection, terminal formatting. |
| `skills/hi-there/SKILL.md` | Agent Skill invoked by phrases like "good morning". Calls the script via Bash and prints its output. |
| `commands/hi-there.md` | Slash command `/powerhelper:hi-there`. Same behavior as the Skill. |
| `README.md` | Updated with `hi-there` usage, dependencies, and cache behavior. |
| `kimi.plugin.json` | Unchanged; new Skill and command are auto-discovered under existing paths. |

---

### Task 1: Create the Python dashboard script

**Files:**
- Create: `tools/hi-there.py`

- [ ] **Step 1: Create the script file**

Create `tools/hi-there.py` with the following content:

```python
#!/usr/bin/env python3
"""hi-there daily terminal dashboard for the PowerHelper plugin."""

import json
import random
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "powerhelper"
CACHE_FILE = CACHE_DIR / "hi-there.json"
CACHE_TTL_HOURS = 24

DEFAULT_LOCATION = "Combs-la-Ville"
WEATHER_URL = "https://wttr.in/{location}?format=3"
NEWS_URL = "http://feeds.bbci.co.uk/news/rss.xml"
NEWS_COUNT = 5

MEMES = [
    r"""
    (\_/)  
    (o.o)  
    (> <)  
    """,
    r"""
     /\_/\
    ( o.o )
     > ^ <
    """,
    r"""
    ___________
   |  OH HAI   |
    -----------
        \
         \
           ^__^
           (oo)\_______
           (__)\       )\/\
               ||----w |
               ||     ||
    """,
    r"""
      ___
     |o o|
     |_<_|_____/
    """,
    r"""
       .-.
      (o o)
      | O \
       \   \
        `~~~'
    """,
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def load_cache() -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data["cached_at"])
        if now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data
    except (KeyError, ValueError, json.JSONDecodeError):
        # Corrupted or malformed cache; will be overwritten.
        pass
    return None


def save_cache(data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["cached_at"] = now().isoformat()
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_weather(location: str) -> str:
    url = WEATHER_URL.format(location=location)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8").strip()
    except urllib.error.URLError as exc:
        return f"Weather unavailable ({exc})"


def fetch_news() -> list[str]:
    try:
        with urllib.request.urlopen(NEWS_URL, timeout=10) as response:
            content = response.read()
        root = ET.fromstring(content)
        titles = []
        for item in root.findall(".//item"):
            title = item.find("title")
            if title is not None and title.text:
                titles.append(title.text.strip())
            if len(titles) >= NEWS_COUNT:
                break
        return titles
    except (urllib.error.URLError, ET.ParseError) as exc:
        return [f"News unavailable ({exc})"]


def render_dashboard(location: str, weather: str, news: list[str]) -> str:
    meme = random.choice(MEMES)
    lines = [
        "┌────────────────────────────────────────────────────────────┐",
        "│  ☀️  Good Morning! Here's your daily briefing              │",
        "├────────────────────────────────────────────────────────────┤",
    ]
    for meme_line in meme.strip("\n").splitlines():
        lines.append(f"│{meme_line:^60}│")
    lines.extend([
        "├────────────────────────────────────────────────────────────┤",
        f"│  🌤️  Weather in {location:<43}│",
        f"│     {weather:<55}│",
        "├────────────────────────────────────────────────────────────┤",
        "│  📰  News                                                   │",
    ])
    for headline in news:
        # Truncate long headlines and pad to fit the box.
        safe = headline.encode("ascii", "replace").decode("ascii")
        truncated = (safe[:53] + "...") if len(safe) > 56 else safe
        lines.append(f"│     • {truncated:<53}│")
    lines.extend([
        "├────────────────────────────────────────────────────────────┤",
        "│  Run /powerhelper:hi-there for a fresh page                │",
        "└────────────────────────────────────────────────────────────┘",
    ])
    return "\n".join(lines)


def main() -> int:
    location = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOCATION

    cached = load_cache()
    if cached:
        weather = cached["weather"]
        news = cached["news"]
    else:
        weather = fetch_weather(location)
        news = fetch_news()
        save_cache({"weather": weather, "news": news})

    print(render_dashboard(location, weather, news))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Validate Python syntax**

Run:

```bash
python3 -m py_compile tools/hi-there.py && echo "syntax OK"
```

Expected output:

```
syntax OK
```

- [ ] **Step 3: Run the script once to verify output and cache creation**

Run:

```bash
python3 tools/hi-there.py
```

Expected outcome:

- A terminal dashboard is printed.
- A cache file is created at `~/.cache/powerhelper/hi-there.json`.

- [ ] **Step 4: Run the script a second time to verify cache usage**

Run:

```bash
python3 tools/hi-there.py
```

Expected outcome:

- Dashboard prints again, faster (no network delay).
- `~/.cache/powerhelper/hi-there.json` still exists.

- [ ] **Step 5: Commit the script**

```bash
git add tools/hi-there.py
git commit -m "feat: add hi-there dashboard Python script"
```

---

### Task 2: Create the `hi-there` Skill

**Files:**
- Create: `skills/hi-there/SKILL.md`

- [ ] **Step 1: Create the Skill file**

Create `skills/hi-there/SKILL.md` with the following content:

```markdown
---
name: hi-there
description: Display a daily terminal dashboard with weather, news, and an ASCII meme
type: prompt
whenToUse: When the user says good morning, hi-there, daily briefing, or asks for a terminal dashboard
arguments:
  - location
---

You are the PowerHelper `hi-there` dashboard.

Run the dashboard script via Bash and print its raw output exactly:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" "$location"
```

If no `$location` is provided, the script defaults to `Combs-la-Ville`.
Do not modify the output. Do not add extra commentary.
```

- [ ] **Step 2: Verify the Skill file has frontmatter delimiters**

Run:

```bash
grep -q "^---$" skills/hi-there/SKILL.md && echo "frontmatter OK" || echo "frontmatter missing"
```

Expected output:

```
frontmatter OK
```

- [ ] **Step 3: Commit the Skill**

```bash
git add skills/hi-there/SKILL.md
git commit -m "feat: add hi-there skill"
```

---

### Task 3: Create the `hi-there` slash command

**Files:**
- Create: `commands/hi-there.md`

- [ ] **Step 1: Create the command file**

Create `commands/hi-there.md` with the following content:

```markdown
---
description: Display the daily hi-there terminal dashboard
---

Run the PowerHelper hi-there dashboard script via Bash and print its raw output exactly:

```bash
python3 "${KIMI_SKILL_DIR}/../tools/hi-there.py" "$ARGUMENTS"
```

If no arguments are provided, the script defaults to `Combs-la-Ville`.
Do not modify the output. Do not add extra commentary.
```

- [ ] **Step 2: Verify the command file exists**

Run:

```bash
test -f commands/hi-there.md && echo "command file exists"
```

Expected output:

```
command file exists
```

- [ ] **Step 3: Commit the command**

```bash
git add commands/hi-there.md
git commit -m "feat: add /powerhelper:hi-there slash command"
```

---

### Task 4: Update the README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read the current README**

Use the `Read` tool on `README.md` to get the current content.

- [ ] **Step 2: Append the `hi-there` section**

Append the following section to the end of `README.md`:

```markdown
## `hi-there` daily dashboard

A terminal dashboard that shows:

- an ASCII meme;
- the current weather in Combs-la-Ville (customizable);
- a short list of public news headlines;
- a 24-hour local cache to avoid repeated network calls.

### Usage

```text
/powerhelper:hi-there
```

Or simply say:

```text
good morning
```

To use a different location:

```text
/skill:hi-there Paris
```

### Requirements

- Python 3 must be installed and on `PATH`.
- Network access to `wttr.in` and `feeds.bbci.co.uk` (only on the first run of the day, or when the cache is stale).

### Cache

The cache lives at `~/.cache/powerhelper/hi-there.json` and is refreshed every 24 hours. Delete it manually to force a refresh.
```

- [ ] **Step 3: Verify the section was appended**

Run:

```bash
grep -q "## \`hi-there\` daily dashboard" README.md && echo "README section OK"
```

Expected output:

```
README section OK
```

- [ ] **Step 4: Commit the README update**

```bash
git add README.md
git commit -m "docs: document hi-there dashboard"
```

---

### Task 5: Validate plugin discovery and diagnostics

**Files:**
- Read: `kimi.plugin.json`
- Read: `skills/hi-there/SKILL.md`
- Read: `commands/hi-there.md`

- [ ] **Step 1: Confirm all new files are present**

Run:

```bash
ls -1 tools/hi-there.py skills/hi-there/SKILL.md commands/hi-there.md
```

Expected output:

```
tools/hi-there.py
skills/hi-there/SKILL.md
commands/hi-there.md
```

- [ ] **Step 2: Confirm the manifest still points to the discovery directories**

Run:

```bash
python3 - <<'PY'
import json
with open('kimi.plugin.json') as f:
    m = json.load(f)
assert m['skills'] == './skills/'
assert m['commands'] == './commands/'
print("manifest discovery paths OK")
PY
```

Expected output:

```
manifest discovery paths OK
```

- [ ] **Step 3: Install/reinstall the plugin locally in Kimi Code CLI**

Inside Kimi Code CLI, run:

```text
/plugins install ./kimi-pluggin-powerhelper
/reload
```

Expected outcome: plugin installs or updates without errors.

- [ ] **Step 4: Check plugin diagnostics**

Inside Kimi Code CLI, run:

```text
/plugins info powerhelper
```

Expected outcome: no manifest or path diagnostics; both `using-powerhelper` and `hi-there` skills are listed, and both commands are registered.

- [ ] **Step 5: Test the slash command**

Inside Kimi Code CLI, run:

```text
/powerhelper:hi-there
```

Expected outcome: a terminal dashboard is printed with weather, news, and an ASCII meme.

- [ ] **Step 6: Test natural invocation**

Inside Kimi Code CLI, run:

```text
good morning
```

Expected outcome: the same dashboard is printed (the Skill auto-triggers).

- [ ] **Step 7: Push all changes to GitHub**

Run:

```bash
git push
```

Expected outcome: all commits are pushed to `origin/main`.

---

## Self-Review

### Spec coverage

| Spec section | Implementing task |
| --- | --- |
| Python script with cache, weather, news, ASCII meme | Task 1 |
| Skill `hi-there` with frontmatter and Bash invocation | Task 2 |
| Slash command `/powerhelper:hi-there` | Task 3 |
| README update | Task 4 |
| Plugin discovery unchanged, diagnostics clean, command/skill tested | Task 5 |

### Placeholder scan

No `TBD`, `TODO`, "implement later", "add appropriate error handling", "write tests for the above", or "similar to Task N" placeholders found.

### Type consistency

- Script argument defaults to `Combs-la-Ville`.
- Skill passes `$location` to the script; defaults handled by the script.
- Command passes `$ARGUMENTS` to the script; defaults handled by the script.
- Cache path is consistent: `~/.cache/powerhelper/hi-there.json`.

### Gap check

- The spec mentions error handling for missing Python; covered by documenting the dependency in the README.
- The spec asks for output entirely in English; the script and docs use English text only.
