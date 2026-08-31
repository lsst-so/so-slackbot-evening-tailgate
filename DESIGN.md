# Evening Tailgate Meeting Bot — Design

## Purpose
Coordinate the daily Evening Tailgate Meeting (16:30, America/Santiago) via Slack. Default is
cancellation; a day-shift observing specialist must actively confirm for it to happen.

## Flow
1. **16:15** — bot posts a reminder to the tailgate channel: meeting starts at 16:30, with a
   "Confirm Meeting" button. Text makes clear that no action = cancelled.
2. **Any day-shift observing specialist** clicks "Confirm Meeting" between 16:15 and 16:25.
   - Bot checks the clicker's membership in a designated Slack User Group (e.g. `@day-obs-specialists`).
   - Not a member → ephemeral message, no state change.
   - Member, first confirm today → bot posts a follow-up message: meeting is happening, with the
     meeting link, and who confirmed it. Original reminder is edited to remove the button.
   - Member, already confirmed by someone else → ephemeral "already confirmed by X".
3. **16:25 (cutoff)** — if nobody confirmed, bot posts an explicit cancellation message and edits
   the original reminder to remove the button. A late click after this point gets an ephemeral
   "too late, already cancelled" reply.

## Key decisions (from requirements discussion, 2026-08-31)
- **Build**: custom Slack bot (Python, Slack Bolt), not Workflow Builder — needed for the
  roster check, the hard cutoff, and per-day state tracking.
- **Permissions**: only members of a Slack User Group may confirm. The group's membership is
  maintained in Slack itself (whoever manages shift rotations updates it), not by the bot.
- **Default behavior**: explicit cancellation message at the 16:25 cutoff, not silence.
- **Meeting link**: fixed, stored in bot config (not looked up per day).
- **Channel**: single fixed channel, stored in bot config.
- **Timezone**: America/Santiago for all scheduling.
- **Hosting**: Slack **Socket Mode** — the bot holds an outbound WebSocket connection to Slack,
  so it needs no public inbound URL/HTTPS endpoint. This fits well behind an observatory
  firewall: run it as a long-lived process (systemd service) on any Linux box with outbound
  internet access — an existing server, a small VM, or a container. No inbound port to open.
- **State**: a local SQLite file tracks each day's status (pending/confirmed/cancelled) so a
  bot restart mid-afternoon doesn't lose track of whether today was already handled.

## Open items for later (not blocking a first version)
- Who maintains the `@day-obs-specialists` Slack User Group membership day to day.
- Whether weekends/holidays need the reminder suppressed entirely (currently: bot posts every
  day; add a skip-list if needed).
- Whether the reminder time (16:15) and cutoff (16:25) should be configurable per-environment —
  currently both are environment variables, so this is already flexible.
