# Handoff: Evening Tailgate Meeting Bot

Written 2026-08-31, at the point where work moves from a Claude (Cowork) cloud session to
Claude Code running on your own machine. This file is meant to be enough context on its own —
paste it into a fresh Claude Code session (or just have it read this file) and it can pick up
immediately without you re-explaining anything.

## What this is

A Slack bot for Vera Rubin Observatory that coordinates the daily Evening Tailgate Meeting
(16:30, America/Santiago). Full behavior spec is in `DESIGN.md` — read that first if anything
below is unclear. Short version: the bot posts a reminder at 16:15 with a "Confirm Meeting"
button; only members of a Slack User Group can click it; if nobody does by 16:25 it posts an
explicit cancellation instead of staying silent; if someone does, it posts the fixed meeting
link.

## Status: implementation complete, not yet deployed or tested against real Slack

Everything below is written and internally verified, but has never talked to the real Slack
API or actually run inside a real Docker daemon — that's the immediate next step now that a
server is available.

### What's done
- `src/tailgate_bot/` — the full bot as an installable package (`app.py`, `config.py`,
  `state.py`, `messages.py`, `jobs.py`, `scheduler.py`, plus `__main__.py`).
  Python, Slack Bolt, Socket Mode (no public inbound URL needed). Entry point:
  `tailgate_bot.app:main`, exposed as the `tailgate-bot` console script.
- `pyproject.toml` — package metadata, dependencies, and the console-script entry point
  (replaces the old flat modules + `requirements.txt`).
- `.env.example` — required configuration.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore` — containerized deployment, state
  persisted on a named volume (`tailgate-data:/data`).
- `tailgate-bot.service` — systemd unit, kept as a non-Docker fallback deployment path.
- `README.md` — step-by-step: creating the Slack app (scopes, Socket Mode, interactivity),
  getting the channel ID and Slack User Group ID, configuring `.env`, running via Docker or
  systemd.
- `DESIGN.md` — the full behavior spec and the reasoning behind each decision.

### What's verified, and how
- All Python files pass `py_compile` (no syntax errors).
- The state machine (SQLite-backed day status: pending/confirmed/cancelled) was exercised with
  a throwaway self-test script covering: first confirm succeeds, duplicate/racing confirms are
  rejected, cutoff correctly no-ops once already resolved, cutoff correctly cancels when nothing
  happened, and a late click after cancellation is rejected. All passed.
- `docker-compose.yml` syntax was validated with `docker compose config`.
- **Bug caught and fixed during Docker verification**: `.env.example` originally hardcoded
  `TAILGATE_DB_PATH=tailgate_state.db`. Because Docker Compose's `env_file` injects that into
  the container's environment, it would have silently overridden the image's `/data` default
  and pointed SQLite state *outside* the mounted volume — losing all state on every container
  rebuild. Now commented out in `.env.example` with an explanation; confirmed via
  `docker compose config` that the variable no longer leaks into the container.
- `app.py` itself could not be imported/exercised end-to-end in the authoring sandbox, because
  `slack_bolt.App()` makes a live `auth.test` call to slack.com at construction time, and that
  sandbox's network policy blocks it. Its logic was reviewed by hand instead — it mirrors the
  `StateStore` transitions that were tested directly.
- A real `docker build` could **not** be run in the authoring sandbox either — no egress to
  Docker Hub / any container registry from there. The Dockerfile was reviewed but never
  actually built.

### Not yet done — this is where you pick up
1. **Create the real Slack app** following `README.md` section 1–2 (Socket Mode, `chat:write` +
   `usergroups:read` scopes, interactivity on, install to workspace, invite bot to channel).
2. **Create/identify the Slack User Group** for day-shift observing specialists and get its ID.
3. **Fill in `.env`** from `.env.example` with real tokens, channel ID, user group ID, and the
   actual meeting link.
4. **First real test**: `docker compose up -d --build` on the new server, then
   `docker compose logs -f` — confirm the scheduler starts and the Socket Mode connection
   comes up cleanly. This is the first time the Dockerfile actually gets built for real.
5. **End-to-end dry run**: temporarily set `TAILGATE_REMINDER_TIME` / `TAILGATE_CUTOFF_TIME` a
   few minutes in the future in `.env`, restart the container, and walk through both paths by
   hand — click Confirm as an authorized user, and separately let one run through to cutoff
   with no click — before trusting it with the real 16:15/16:25 schedule.
6. Once confirmed working, restore the real reminder/cutoff times.

### Known open items (not blockers, just undecided)
- Who maintains the day-shift Slack User Group's membership day to day.
- Whether the bot should skip weekends/holidays entirely (currently posts every day — see the
  note in `DESIGN.md` and `scheduler.py` for where a day-of-week check would go).

## Where the rest of the context lives
The full requirements discussion and design rationale is also saved as a doc in the
"Vera Rubin Observatory" Claude project (`claude/tailgate-bot-design.md`) if you're picking this
up from claude.ai — but `DESIGN.md` in this folder has the same content, so nothing is lost by
working from this folder alone.
