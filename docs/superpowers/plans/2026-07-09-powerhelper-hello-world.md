# PowerHelper Hello-World Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap a minimal Kimi Code CLI plugin containing an auto-loaded Skill and a slash command, plus a README explaining how to install and use it.

**Architecture:** Static plugin manifest + SKILL.md + command markdown; no executable code. The plugin is installed from a local directory or from a GitHub URL and is validated through Kimi Code's `/plugins info` diagnostics.

**Tech Stack:** Markdown, JSON, Git.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `kimi.plugin.json` | Plugin manifest: id, version, skills path, session-start skill, commands path, display metadata. |
| `skills/using-powerhelper/SKILL.md` | Agent Skill loaded at session start; defines when and how to greet the user. |
| `commands/hello.md` | Slash command `/powerhelper:hello`; sends a hello-world prompt to the model. |
| `README.md` | Learning summary, repo structure, install and usage instructions. |

---

### Task 1: Create the plugin manifest

**Files:**
- Create: `kimi.plugin.json`

- [ ] **Step 1: Write the manifest file**

Create `kimi.plugin.json` with the following content:

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
  "interface": {
    "displayName": "PowerHelper",
    "shortDescription": "Hello-world plugin for learning Kimi Code plugins"
  }
}
```

- [ ] **Step 2: Validate JSON syntax**

Run:

```bash
python3 -m json.tool kimi.plugin.json > /dev/null && echo "valid JSON"
```

Expected output:

```
valid JSON
```

- [ ] **Step 3: Commit the manifest**

```bash
git add kimi.plugin.json
git commit -m "feat: add plugin manifest"
```

---

### Task 2: Create the auto-loaded Skill

**Files:**
- Create: `skills/using-powerhelper/SKILL.md`

- [ ] **Step 1: Create the Skill directory and file**

Create `skills/using-powerhelper/SKILL.md` with the following content:

```markdown
---
name: using-powerhelper
description: Greet the user and answer basic questions about the PowerHelper plugin
type: prompt
whenToUse: When the user greets, says hello, or asks what the PowerHelper plugin can do
---

You are the PowerHelper plugin. Respond in a friendly, concise manner.

- If the user greets you, says "hello", "hi", "salut", or similar, reply with exactly: "Hello, World! from PowerHelper 👋".
- If the user asks what you can do, explain that this is a learning plugin for Kimi Code CLI and that it exposes the slash command `/powerhelper:hello`.
- Keep responses short and avoid adding extra noise.
```

- [ ] **Step 2: Verify the file exists and has frontmatter delimiters**

Run:

```bash
grep -q "^---$" skills/using-powerhelper/SKILL.md && echo "frontmatter OK" || echo "frontmatter missing"
```

Expected output:

```
frontmatter OK
```

- [ ] **Step 3: Commit the Skill**

```bash
git add skills/using-powerhelper/SKILL.md
git commit -m "feat: add auto-loaded powerhelper skill"
```

---

### Task 3: Create the slash command

**Files:**
- Create: `commands/hello.md`

- [ ] **Step 1: Create the command directory and file**

Create `commands/hello.md` with the following content:

```markdown
---
description: Say hello from the PowerHelper plugin
---

Say "Hello, World! from PowerHelper 👋" and offer to explain how the plugin works.
```

- [ ] **Step 2: Verify the command file exists**

Run:

```bash
test -f commands/hello.md && echo "command file exists"
```

Expected output:

```
command file exists
```

- [ ] **Step 3: Commit the command**

```bash
git add commands/hello.md
git commit -m "feat: add /powerhelper:hello slash command"
```

---

### Task 4: Write the README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the README file**

Create `README.md` with the following content:

```markdown
# PowerHelper — Kimi Code CLI Hello-World Plugin

A minimal custom plugin for [Kimi Code CLI](https://www.kimi.com/code/) to learn the plugin system. It bundles:

- an **Agent Skill** loaded automatically at session start;
- a **slash command** you can trigger manually.

No executable code, no external dependencies: this is the simplest possible plugin shape.

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
│   └── using-powerhelper/
│       └── SKILL.md
└── commands/
    └── hello.md
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

## Resources

- [Plugins documentation](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html)
- [Skills documentation](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html)
```

- [ ] **Step 2: Check the README renders without broken sections**

Run:

```bash
grep -q "^# PowerHelper" README.md && echo "README header OK"
```

Expected output:

```
README header OK
```

- [ ] **Step 3: Commit the README**

```bash
git add README.md
git commit -m "docs: add README with install and usage instructions"
```

---

### Task 5: Initialize the Git repository and push to remote

**Files:**
- Modify: `.git/` (repository initialization)
- Modify: `README.md` (optional badge or remote link updates only if needed)

- [ ] **Step 1: Initialize the local repository and add the remote**

Run:

```bash
git init
git branch -M main
git remote add origin git@github.com:superT0f/kimi-pluggin-powerhelper.git
```

Expected state:

```bash
git remote -v
```

Expected output:

```
origin  git@github.com:superT0f/kimi-pluggin-powerhelper.git (fetch)
origin  git@github.com:superT0f/kimi-pluggin-powerhelper.git (push)
```

- [ ] **Step 2: Verify the commit history**

Run:

```bash
git log --oneline
```

Expected output (order may vary):

```
... docs: add README with install and usage instructions
... feat: add /powerhelper:hello slash command
... feat: add auto-loaded powerhelper skill
... feat: add plugin manifest
```

- [ ] **Step 3: Push to GitHub**

Run:

```bash
git push -u origin main
```

Expected outcome: the local `main` branch is pushed to `origin/main` without errors.

---

### Task 6: Validate the plugin locally

**Files:**
- Read: `kimi.plugin.json`
- Read: `skills/using-powerhelper/SKILL.md`
- Read: `commands/hello.md`

- [ ] **Step 1: Confirm all expected files are present**

Run:

```bash
ls -1 kimi.plugin.json skills/using-powerhelper/SKILL.md commands/hello.md README.md
```

Expected output:

```
kimi.plugin.json
skills/using-powerhelper/SKILL.md
commands/hello.md
README.md
```

- [ ] **Step 2: Install the plugin locally in Kimi Code CLI**

Inside Kimi Code CLI, run:

```
/plugins install ./kimi-pluggin-powerhelper
/reload
```

Expected outcome: plugin installs without errors.

- [ ] **Step 3: Check plugin diagnostics**

Inside Kimi Code CLI, run:

```
/plugins info powerhelper
```

Expected outcome: no manifest or path diagnostics; plugin shows as enabled.

- [ ] **Step 4: Test the Skill and the slash command**

Inside Kimi Code CLI, run:

```
hello
```

Expected response contains:

```
Hello, World! from PowerHelper 👋
```

Then run:

```
/powerhelper:hello
```

Expected response contains:

```
Hello, World! from PowerHelper 👋
```

---

## Self-Review

### Spec coverage

| Spec section | Implementing task |
| --- | --- |
| Plugin manifest with id, version, skills path, session-start skill, commands path, display metadata | Task 1 |
| Directory-form Skill with frontmatter and body | Task 2 |
| Slash command `/powerhelper:hello` | Task 3 |
| README with structure, install, usage, resources | Task 4 |
| Git init + push to remote | Task 5 |
| Local validation via `/plugins info` and usage tests | Task 6 |

### Placeholder scan

No `TBD`, `TODO`, "implement later", "add appropriate error handling", "write tests for the above", or "similar to Task N" placeholders found.

### Consistency check

- Plugin id `powerhelper` matches in manifest (`name`), README references, and expected slash command name.
- Skill name `using-powerhelper` matches in manifest `sessionStart.skill` and in `SKILL.md` frontmatter.
- Paths `./skills/` and `./commands/` match the actual directory layout.
