# Handoff: Evening Tailgate Meeting Bot

Last updated 2026-08-31. This file is meant to be enough context on its own — paste it into a
fresh Claude Code session (or have it read this file) and it can pick up without you
re-explaining anything.

## What this is

A Slack bot for Vera Rubin Observatory that coordinates the daily Evening Tailgate Meeting
(16:30, America/Santiago). Full behavior spec is in `DESIGN.md` — read that first if anything
below is unclear. Short version:

- At 16:15 the bot posts a reminder to the tailgate channel with a "Confirm Meeting" button,
  @-mentioning the day-obs user group (and, optionally, a science-support shift group) so
  their members are notified.
- Only members of `DAY_OBS_USERGROUP_ID` may confirm. An unauthorized clicker gets a DM
  explaining they can't. `SCI_SUP_SHIFT_USERGROUP_ID` (if set) is notified but cannot confirm.
- First authorized confirm → the bot posts a "confirmed" message with the meeting link (Zoom
  link, link preview suppressed) and who confirmed, and edits the reminder to drop the button.
- If nobody confirms by 16:25, the bot posts an explicit cancellation and drops the button.
- The confirmation and cancellation messages also @-mention the groups.

## Status: running live against real Slack from a developer laptop; not yet on a persistent host

The bot has been run against the real Slack workspace and works end to end (see "Verified"
below). It currently only runs when someone starts it by hand on their machine. The next
piece of work is packaging it to run continuously on **Phalanx** (see "Next work").

### What's done
- `src/tailgate_bot/` — the full bot as an installable package (`app.py`, `config.py`,
  `state.py`, `messages.py`, `jobs.py`, `scheduler.py`, `__main__.py`). Python, Slack Bolt,
  Socket Mode (no public inbound URL), APScheduler for the two daily jobs, SQLite for
  per-day state. Entry point `tailgate_bot.app:main`, exposed as the `tailgate-bot` console
  script and `python -m tailgate_bot`.
- `pyproject.toml` — package metadata, dependencies (`slack-bolt`, `APScheduler`, `tzdata`),
  the `tailgate-bot` console script, and the `test` extra. Replaces the old flat modules +
  `requirements.txt`.
- `tests/` + `.github/workflows/test.yaml` — 41 Slack-free tests, run in CI on Python
  3.11–3.13. `.github/workflows/lint.yaml` runs flake8 (repo `setup.cfg`).
- `.env.example` — every config variable, with comments.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore` — container build (`pip install .`,
  runs `tailgate-bot` as a non-root user; SQLite state on a named volume at `/data`).
- `tailgate-bot.service` — systemd unit, kept as a non-container fallback.
- `README.md` — Slack app setup (Socket Mode, app-level token, `chat:write` +
  `usergroups:read` + `im:write` scopes, interactivity), getting channel / user-group IDs,
  configuring `.env`, running locally, and deploying via Docker or systemd.
- `DESIGN.md` — the behavior spec and the reasoning behind each decision.

### Configuration (all via environment variables — see `.env.example`)
Required: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `TAILGATE_CHANNEL_ID`,
`DAY_OBS_USERGROUP_ID`, `TAILGATE_MEETING_LINK`.
Optional: `SCI_SUP_SHIFT_USERGROUP_ID` (notify-only second group),
`TAILGATE_MENTION_USERGROUP` (default on), `TAILGATE_TIMEZONE` (default `America/Santiago`),
`TAILGATE_REMINDER_TIME` (`16:15`), `TAILGATE_CUTOFF_TIME` (`16:25`),
`TAILGATE_MEETING_TIME_LABEL` (`16:30`), `TAILGATE_DB_PATH` (leave unset — each deployment
picks its own default; the container uses `/data/tailgate_state.db`).

### Verified
- `flake8` clean; `pytest` (41 tests) green locally and in CI. The suite covers the state
  machine (first confirm wins, racing/duplicate confirms rejected, cutoff no-ops once
  resolved, cutoff cancels when nothing happened, late click rejected, state survives a DB
  reopen), the Block Kit builders (confirm button, group mentions on all three messages,
  the mention toggle, meeting link, times), both scheduled jobs driven by a fake Slack
  client, scheduler wiring (job ids/names, cron times, timezone), and `load_config`
  (defaults, required-var errors, `TAILGATE_MENTION_USERGROUP` parsing, the second group
  being mentioned but not an authorizer).
- **Live Slack run** from a laptop with the real `.env`: Socket Mode connects; the 16:15
  reminder posts and @-mentions both groups; an authorized confirm posts the "confirmed" +
  Zoom link message (no link preview) and strips the button; letting it run to the cutoff
  posts the cancellation and strips the button; an unauthorized click gets the DM. The
  scheduler fires both jobs on time.
- Not covered by automated tests: `app.py` / the `handle_confirm` button handler — importing
  the module runs `load_config()` and `slack_bolt.App()` (a live `auth.test`) at import, so
  CI can't import it. Its logic mirrors the `StateStore` transitions and message builders
  that are tested directly, and it has been exercised in the live run above. Making it
  CI-testable needs the lazy-bootstrap refactor listed under open items.

## Next work: run it on Phalanx

**Phalanx** (docs: phalanx.lsst.io) is Rubin/SQuaRE's GitOps platform for running services
on Kubernetes. Each service is a Helm chart under `applications/<name>/` in the
`lsst-sqre/phalanx` repo; Argo CD continuously deploys what's in git. Non-secret config lives
in per-environment `values-<env>.yaml`; secrets are declared in the chart's `secrets.yaml`
and pulled from Vault (SQuaRE's source of truth is 1Password) into a Kubernetes Secret by the
Vault Secrets Operator. Container images are built by GitHub Actions and pushed to the GitHub
Container Registry. SQuaRE's own Slack bots (e.g. Squarebot) run in the `roundtable`
environment.

This bot is a good fit in one respect and unusual in another: it's a single long-running
process with only *outbound* network (Socket Mode WebSocket + Slack Web API + APScheduler),
so it needs **no Ingress, no Gafaelfawr, no route** — simpler than most Phalanx apps. But
SQuaRE's convention for Slack bots is the Squarebot framework (Slack events routed through
Kafka to backend consumers), not Socket Mode. First question to settle with SQuaRE: is a
Socket Mode + APScheduler service acceptable on `roundtable`, or do they want this rebuilt on
the Squarebot pattern?

Assuming Socket Mode is accepted, the work is roughly:

1. **Publish the image.** Add a GitHub Actions workflow in *this* repo to build the
   `Dockerfile` and push to `ghcr.io/lsst-so/so-slackbot-evening-tailgate` on release/tag
   (SQuaRE has a reusable build-and-push action). The `Dockerfile` already produces an
   installable package running as non-root; `tzdata` is a dependency so `zoneinfo` works on
   the slim base image. Verify the build once a Docker daemon is available — it has never
   actually been built.
2. **Create the Phalanx application** — a PR to `lsst-sqre/phalanx` adding
   `applications/so-slackbot-evening-tailgate/`: `Chart.yaml`, a `Deployment` template
   (1 replica, `strategy: Recreate`), `values.yaml` for the non-secret config
   (`TAILGATE_CHANNEL_ID`, `DAY_OBS_USERGROUP_ID`, `SCI_SUP_SHIFT_USERGROUP_ID`,
   `TAILGATE_MEETING_LINK`, the time/timezone vars), `values-<env>.yaml`, and `secrets.yaml`
   declaring `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`. Register it in
   `environments/values-<env>.yaml` and add a docs page. Model it on a small existing app
   (`squarebot`, `mobu`, `templatebot`).
3. **Secrets** — get `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` into Vault via SQuaRE's process;
   the chart surfaces them as env vars. No code change: `config.load_config()` already reads
   them from the environment.
4. **State persistence** — the SQLite file only needs to survive a same-day restart. Simplest
   is a small `PersistentVolumeClaim` mounted at `/data` with
   `TAILGATE_DB_PATH=/data/tailgate_state.db` (works with 1 replica + `Recreate`).
   Alternative: accept that a mid-afternoon pod restart loses the day's state (worst case: a
   duplicate reminder or a redundant cancellation) and drop the volume. Decide with SQuaRE.
5. **Deploy to a dev/int environment first**, watch the Argo CD sync and pod logs for
   `⚡️ Bolt app is running!`, do the timed dry-run (`TAILGATE_REMINDER_TIME` /
   `TAILGATE_CUTOFF_TIME` a few minutes out via the env), then promote to the real
   environment and restore `16:15` / `16:25`.

`docker-compose.yml` and `tailgate-bot.service` stay in the repo as the non-Phalanx fallback.

### Known open items (not blockers)
- **Deployment pattern**: Socket Mode + APScheduler vs. the Squarebot/Kafka pattern — confirm
  with SQuaRE (see above).
- **Which Phalanx environment** the bot should live in, and who owns its Vault secret entries.
- Who maintains the day-shift Slack user group's membership day to day.
- Whether the bot should skip weekends/holidays (currently posts every day — `DESIGN.md` and
  `scheduler.py` note where a day-of-week check would go).
- `app.py` builds `cfg`, `store`, and the Bolt `App` at import time. Moving that into `main()`
  (register `handle_confirm` from inside `main`, pass `cfg`/`store` via closure) would let the
  handler be unit-tested in CI without real Slack credentials.

## Where the rest of the context lives
The original requirements discussion and design rationale is also saved as a doc in the
"Vera Rubin Observatory" Claude project (`claude/tailgate-bot-design.md`) — but `DESIGN.md`
in this folder has the same content, so nothing is lost by working from this folder alone.
