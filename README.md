# PowerHelper — Kimi Code CLI Hello-World Plugin

A minimal custom plugin for [Kimi Code CLI](https://www.kimi.com/code/) to learn the plugin system. It bundles:

- an **Agent Skill** loaded automatically at session start;
- a **slash command** you can trigger manually;
- a **daily terminal dashboard** Skill/command (`hi-there`).

## What is a Kimi Code plugin?

A plugin is a directory (or zip) that contains a manifest and optional resources:

- `kimi.plugin.json` — the manifest that describes the plugin.
- `SKILL.md` files — reusable instructions the model can invoke automatically or on demand.
- `commands/*.md` files — prompt templates exposed as `/plugin:command` slash commands.
- optional `mcpServers` for real tools, or `hooks` for lifecycle events.

## Repository structure

```
kimi-pluggin-powerhelper/
├── README.md
├── kimi.plugin.json
├── skills/
│   ├── using-powerhelper/
│   │   └── SKILL.md
│   └── hi-there/
│       └── SKILL.md
├── commands/
│   ├── hello.md
│   └── hi-there.md
├── screens/
│   ├── 1.png
│   ├── 2.png
│   ├── 3.png
│   └── 4.png
└── tools/
    └── hi-there.py
```

## Installation

### From a local directory

Inside Kimi Code CLI, run:

```
/plugins install ./kimi-pluggin-powerhelper
```

Then reload the session:

```
/reload
```

### From GitHub

```
/plugins install https://github.com/superT0f/kimi-pluggin-powerhelper
```

Then reload:

```
/reload
```

## Usage

### Auto-loaded Skill

Once the plugin is enabled, greet Kimi Code:

```
hello
```

It should reply:

```
Hello, World! from PowerHelper 👋
```

### Slash command

Run the command explicitly:

```
/powerhelper:hello
```

## Verification

Check the plugin diagnostics:

```
/plugins info powerhelper
```

A correct install shows no manifest errors.

## `hi-there` daily dashboard + Phrase of the Day game

A terminal dashboard that shows:

- an ASCII meme;
- the current weather in Combs-la-Ville (customizable);
- a short list of public news headlines;
- a 24-hour local cache to avoid repeated network calls;
- the **Phrase of the Day** mini-game.

### Dashboard usage

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

### Player profile

The first time you run `hi-there`, the assistant asks a few profile questions before showing the dashboard. The questions are driven by `.data/player.md`, so you can add new fields later; the assistant will ask for any new required field on the next run.

Supported field types:

| type | usage |
|---|---|
| `text` | free text answer |
| `number` | numeric answer, can be optional |
| `yes/no` | boolean answer |
| `enum:a,b,c` | choose one of the listed options |

Current fields:

- **pseudo** — free text
- **gender** — free text (LGBTQA+ friendly)
- **age** — optional number
- **style** — `serious`, `relaxed` or `casual`
- **theme** — `light` or `dark`

Your answers are stored locally in `.data/player.json` and shown in the dashboard header.

### Phrase of the Day game

Each day the Skill asks:

1. "What was yesterday's phrase?"
2. "What will tomorrow's phrase be?"

If you remember yesterday's phrase, your streak increases and your win is recorded in `.data/hall-of-fame.md`.

#### First day

On the first run, the game is explained in English and you are asked to set tomorrow's phrase directly.

#### Example flow

```text
good morning
# dashboard + "What was yesterday's phrase?"

the early bird catches the worm
# "Correct! Streak: 3" + "What will tomorrow's phrase be?"

a journey of a thousand miles begins with a single step
# "Tomorrow's phrase is set. See you tomorrow!"
```

### Requirements

- Python 3 must be installed and on `PATH`.
- Network access to `wttr.in` and `feeds.bbci.co.uk` (only on the first dashboard run of the day, or when the cache is stale).

### Cache

The dashboard cache lives at `~/.cache/powerhelper/hi-there.json`.
The game state lives at `~/.cache/powerhelper/hi-there-game.json`.
The player profile values live at `.data/player.json`.
All are refreshed automatically.

## Screenshots

### Daily dashboard (`good morning`)

![Dashboard with ASCII meme, weather and news](screens/1.png)

### Phrase of the Day — first-run explanation

![Mini-game explanation](screens/2.png)

### Setting tomorrow's phrase

![Tomorrow's phrase confirmation](screens/3.png)

### Installing from GitHub and verifying the plugin

![Plugin install and info](screens/4.png)

## Resources

- [Plugins documentation](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html)
- [Skills documentation](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)
