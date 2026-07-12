---
name: rtk
description: Use the rtk CLI proxy to keep shell output compact and context-friendly
type: prompt
whenToUse: Whenever the user or another skill asks to run a shell command that may produce long, noisy, or repetitive output (builds, tests, logs, git, file listings, dependency trees, etc.)
---

You have access to **rtk** (`/home/tof/.local/bin/rtk`, version 0.43.0), a CLI proxy that filters and summarizes command output before it reaches the context window.

## Default rule

When a shell command is requested, prefer its `rtk` equivalent. This reduces token noise while keeping the useful information.

Common mappings:

| Native command | RTK equivalent |
|---|---|
| `ls -la ...` | `rtk ls ...` |
| `tree ...` | `rtk tree ...` |
| `find ...` | `rtk find ...` |
| `git log ...` | `rtk git log ...` |
| `git status` | `rtk git status` |
| `git diff ...` | `rtk diff ...` or `rtk git diff ...` |
| `npm run <script>` | `rtk npm run <script>` |
| `pnpm <cmd>` | `rtk pnpm <cmd>` |
| `npx <cmd>` | `rtk npx <cmd>` |
| `pytest ...` | `rtk pytest ...` |
| `jest ...` | `rtk jest ...` |
| `vitest ...` | `rtk vitest ...` |
| `tsc ...` | `rtk tsc ...` |
| `eslint ...` | `rtk lint ...` |
| `prettier --check ...` | `rtk prettier ...` |
| `docker logs ...` | `rtk docker logs ...` |
| `docker ps` | `rtk docker ps` |
| `kubectl ...` | `rtk kubectl ...` |
| `curl ...` | `rtk curl ...` |
| `cat <file>` / `tail -n N <file>` | `rtk read <file>` |
| `env` | `rtk env` |
| arbitrary long command | `rtk summary "<command>"` |
| arbitrary command, raw output | `rtk run "<command>"` |

## When NOT to use rtk

- The user explicitly asks for **full, unfiltered output**.
- The command is a short, deterministic one-liner with negligible output (e.g. `pwd`, `date`, `echo`).
- The command is interactive or requires a TTY in a way rtk cannot proxy safely.

## How to execute

Use the Bash tool. Pass the rtk command directly:

```bash
rtk ls -la
```

Do not prepend the native command unless the user insists. If a specialized rtk subcommand exists, use it. Otherwise fall back to `rtk summary "..."` or `rtk run "..."`.

## Ultra-compact mode

If the output is still too large, add `--ultra-compact`:

```bash
rtk --ultra-compact npm run build
```
