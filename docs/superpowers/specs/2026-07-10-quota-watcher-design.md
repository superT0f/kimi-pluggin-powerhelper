# PowerHelper Quota Watcher — Design Spec

Date: 2026-07-10  
Status: approved

## Goal

Add a PowerHelper skill that alerts the user when their daily or weekly token quota reaches 70%, then at every 5% increment (75%, 80%, 85%, 90%, 95%, 100%). The skill relies on the user pasting the output of Kimi Code CLI's internal `/usage` command.

## Context

Kimi Code CLI provides `/usage` to display token usage and quota, but there is no public API to fetch it programmatically. Plugins can declare hooks on lifecycle events (`SessionStart`, `Stop`, etc.) and add Skills/Commands. This design works within those constraints.

## Architecture

```
tools/
├── hi-there.py
├── dungeon/
└── quota.py              # parsing + threshold logic
skills/
├── using-powerhelper/
├── hi-there/
├── dungeon/
└── quota-watch/          # session-start + keyword skill
    └── SKILL.md
commands/
├── hello.md
├── hi-there.md
├── dungeon.md
└── quota.md              # slash command /powerhelper:quota
.data/
└── quota-alerts.json     # last alerted thresholds + turn counter
tests/
└── test_quota.py         # unit tests for parsing
```

## Parsing `/usage`

The tool accepts raw `/usage` output via stdin or argument and extracts:

- `daily_used`, `daily_total`, `daily_pct`
- `weekly_used`, `weekly_total`, `weekly_pct`

Supported formats are case-insensitive, with or without `%`, and tolerant to line ordering. Example:

```text
Daily usage: 12345 / 20000 tokens (61.7%)
Weekly usage: 45678 / 100000 tokens (45.7%)
```

## Threshold Logic

- First alert at **70%**.
- Subsequent alerts at each **5% tier** above 70%: 75%, 80%, 85%, 90%, 95%, 100%.
- A tier is alerted only once per window (`daily`/`weekly`) until the quota resets.
- Reset is detected when the parsed percentage drops significantly (more than 10 points below the last alerted tier) or when `used` decreases.
- Output:
  - Alert message if a new tier is crossed.
  - OK message if no new tier is crossed.
  - Help message if the text cannot be parsed.

## Triggers

- **Session start**: `quota-watch` is declared as `sessionStart.skill` in `kimi.plugin.json`. On startup it reads `.data/quota-alerts.json`. If the last alert was ≥ 70%, it reminds the user to run `/usage`.
- **Keywords** (`quota`, `usage`, `daily check`): the skill triggers, politely asks for the `/usage` output, then calls `tools/quota.py`.
- **Slash command** `/powerhelper:quota`: the user pastes `/usage` output as arguments. The command calls `tools/quota.py`.
- **Hook `Stop`**: a plugin hook defined in `kimi.plugin.json` runs `tools/quota.py remind` every 10 turns. The script increments a counter in `.data/quota-alerts.json` and prints a discreet reminder: *“Tip: run /usage and say ‘quota’ to check your daily/weekly token usage.”*

## Alert Storage

`.data/quota-alerts.json` stores:

```json
{
  "daily": {
    "last_alert_pct": 75,
    "last_alert_date": "2026-07-09",
    "turn_counter": 7
  },
  "weekly": {
    "last_alert_pct": 70,
    "last_alert_date": "2026-07-09",
    "turn_counter": 7
  }
}
```

- `last_alert_pct`: last tier that triggered an alert.
- `last_alert_date`: ISO date of the last alert.
- `turn_counter`: turns since the last `Stop` hook reminder.

## Plugin Manifest Changes

`kimi.plugin.json` is updated to:

- Declare `quota-watch` as `sessionStart.skill`.
- Add a `hooks` entry for the `Stop` event every 10 turns.

## Error Handling

- **No data**: if the user does not provide `/usage` output, the skill asks for it.
- **Unrecognized format**: the tool returns a help message showing what text to paste.
- **Silent hook**: if the turn counter is not a multiple of 10, the `Stop` hook prints nothing.

## Tests

`tests/test_quota.py` covers:

- Parsing multiple `/usage` formats.
- Tier calculation and reset detection.
- Turn counter increment in reminder mode.
