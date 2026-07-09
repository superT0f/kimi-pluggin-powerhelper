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
