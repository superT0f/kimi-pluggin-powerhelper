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

## Resources

- [Plugins documentation](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html)
- [Skills documentation](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)
