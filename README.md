# Evening Tailgate Meeting Bot

Posts a daily reminder for the Evening Tailgate Meeting. The meeting is cancelled by
default; a day-shift observing specialist must click "Confirm Meeting" for it to happen.
See `DESIGN.md` for the full behavior spec and the decisions behind it.

Runs as a long-lived Python process using Slack **Socket Mode** — no public URL or open
inbound port required, so it works fine behind the observatory firewall.

## 1. Create the Slack app

1. Go to https://api.slack.com/apps → **Create New App** → **From scratch**.
2. Name it (e.g. "Tailgate Bot") and pick your workspace.
3. **Socket Mode**: under *Settings → Socket Mode*, turn it on.
4. **App-level token**: under *Settings → Basic Information → App-Level Tokens*,
   click **Generate Token and Scopes**, name it (e.g. `socket-mode`), add the
   **`connections:write`** scope, and generate. Copy the token (starts with
   `xapp-`, shown only once) into `SLACK_APP_TOKEN`. Turning on Socket Mode may
   prompt you to create this token directly; if it didn't, this is where it
   lives.
5. **Bot scopes**: under *Features → OAuth & Permissions → Scopes → Bot Token Scopes*, add:
   - `chat:write` (post and update messages)
   - `usergroups:read` (check who's in the day-shift user group)
6. **Interactivity**: under *Features → Interactivity & Shortcuts*, turn it on. With
   Socket Mode enabled you don't need a Request URL.
7. Install the app to your workspace (*Settings → Install App*). Copy the **Bot User OAuth
   Token** (starts with `xoxb-`) into `SLACK_BOT_TOKEN`.
8. Invite the bot to the tailgate channel: `/invite @Tailgate Bot`.

## 2. Get the channel ID and user group ID

- Channel ID: open the channel in Slack, click the channel name → scroll to the bottom of
  the "About" tab → copy the Channel ID. (Or right-click the channel → "Copy link"; the ID
  is the last path segment.)
- User Group ID: create or reuse a Slack User Group for day-shift observing specialists
  (*People & user groups* in your workspace admin, or `/` command in Slack). Its ID
  (starts with `S`) is visible via the Slack API's `usergroups.list`, or ask a workspace
  admin — it's not shown directly in the UI.

## 3. Configure

```bash
cp .env.example .env
# edit .env: SLACK_BOT_TOKEN, SLACK_APP_TOKEN, TAILGATE_CHANNEL_ID,
#            DAY_OBS_USERGROUP_ID, TAILGATE_MEETING_LINK
```

## 4. Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .                    # installs the `tailgate-bot` console script
set -a; source .env; set +a
tailgate-bot                     # or: python -m tailgate_bot
```

The bot is packaged as `tailgate_bot` under `src/`; `pip install .` reads its
dependencies and entry point from `pyproject.toml`. For iterative work use
`pip install -e .` so code edits take effect without reinstalling.

You should see log lines confirming the scheduler started with the configured reminder
and cutoff times. Leave it running — it wakes up on its own at the scheduled times each
day and also handles button clicks in real time via the Socket Mode connection.

## Tests

```bash
pip install '.[test]'
pytest
```

The suite is Slack-free — it exercises the state machine, the Block Kit builders,
the two scheduled jobs (with a fake Slack client), the scheduler wiring, and config
loading. It runs on every push and pull request via `.github/workflows/test.yaml`
(Python 3.11–3.13). Testing against a real Slack workspace is the manual dry-run in
`HANDOFF.md`.

## 5. Deploy as an always-on service

Any always-on Linux machine with outbound internet access works — an existing
observatory server, a small VM, or a container. No inbound networking is required
because of Socket Mode (no ports to publish, no reverse proxy, no TLS cert to manage).

### Option A: Docker (recommended)

A `Dockerfile` and `docker-compose.yml` are included. The container runs as a
non-root user and keeps its SQLite state file on a named volume (`tailgate-data`)
so it survives restarts and image rebuilds.

```bash
cp .env.example .env
# edit .env as in step 3 above

docker compose up -d --build
docker compose logs -f          # confirm the scheduler started and Socket Mode connected
```

To update after a code change: `docker compose up -d --build` again — the state
volume is untouched by a rebuild. To stop: `docker compose down` (add `-v` only if
you actually want to wipe the stored state).

Without Compose, the equivalent plain `docker` commands are:

```bash
docker build -t tailgate-bot .
docker run -d --name tailgate-bot --restart unless-stopped \
  --env-file .env -v tailgate-data:/data tailgate-bot
```

### Option B: systemd (bare metal, no Docker)

A sample `tailgate-bot.service` unit is included for a host without Docker:

```bash
sudo mkdir -p /opt/tailgate-bot
sudo cp -r . /opt/tailgate-bot
cd /opt/tailgate-bot
sudo python3 -m venv .venv
sudo .venv/bin/pip install .
sudo useradd --system --no-create-home tailgate-bot   # if it doesn't exist yet
sudo chown -R tailgate-bot:tailgate-bot /opt/tailgate-bot
sudo cp tailgate-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tailgate-bot
sudo systemctl status tailgate-bot
```

## Notes

- State for "has today been confirmed/cancelled yet" lives in a small SQLite file
  (`tailgate_state.db` next to the app when run directly, or `/data/tailgate_state.db`
  on a mounted volume in the Docker setup) so a restart mid-afternoon doesn't lose
  track of where today stands.
- The bot currently posts every day, including weekends. If that's not wanted, add a
  day-of-week check in `jobs.post_reminder` / `scheduler.py` — flagged as an open item
  in `DESIGN.md`.
- Reminder time, cutoff time, and the meeting time label are independently configurable
  via environment variables if 16:15 / 16:25 / 16:30 ever change.
