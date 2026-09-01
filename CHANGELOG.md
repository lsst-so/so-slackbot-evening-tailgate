# Change log

All notable changes to this project are documented here.

This file is assembled from news fragments in `changelog.d/` by
[scriv](https://scriv.readthedocs.io/) at release time; see `RELEASE.md`. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

<!-- scriv-insert-here -->

<a id='changelog-0.1.1'></a>
## 0.1.1 (2026-09-01)

### Other changes

- Standardised on Python 3.13: `requires-python` is now `>=3.13`, the container image is built `FROM python:3.13-slim`, and CI runs the test suite on 3.13 only (was 3.11–3.13).

<a id='changelog-0.1.0'></a>
## 0.1.0 (2026-09-01)

### New features

- First tagged release of the Evening Tailgate Meeting bot.
- Posts a daily reminder to the tailgate channel with a "Confirm Meeting" button, @-mentioning the day-obs Slack user group (and an optional science-support shift group) so their members are notified.
- The meeting is cancelled by default: only members of `DAY_OBS_USERGROUP_ID` may confirm, and the first authorized confirm posts the meeting link (with the link preview suppressed) and strips the button.
- If nobody confirms by the cutoff time, the bot posts an explicit cancellation and strips the button.
- An unauthorized click gets a direct message explaining they cannot confirm.
- Runs as a single long-lived process over Slack Socket Mode (no inbound URL), with APScheduler driving the reminder and cutoff jobs and per-day state kept in SQLite.
- Reminder time, cutoff time, meeting-time label, timezone, the mention toggle, and the state database path are all configurable via environment variables.
- Ships a `Dockerfile`, `docker-compose.yml`, and a `tailgate-bot.service` systemd unit for deployment.

### Other changes

- Project version is now derived from the Git release tag via setuptools-scm.
- Introduced a scriv-based changelog workflow (`changelog.d/` news fragments collected into `CHANGELOG.md`).
