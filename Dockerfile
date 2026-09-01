# syntax=docker/dockerfile:1
FROM python:3.13-slim

# tini: a real PID 1 that reaps zombies and forwards SIGTERM to the bot, so
# `docker stop` / a Kubernetes pod eviction shuts the Socket Mode connection
# down promptly instead of waiting out the kill grace period.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# The SQLite state file lives under /data so it survives a restart/upgrade.
# Under Docker or Compose (below) or systemd that path is a mounted named
# volume; under Phalanx a PersistentVolumeClaim is mounted over the same
# path. It only has to outlive a same-day restart.
ENV TAILGATE_DB_PATH=/data/tailgate_state.db

RUN useradd --system --create-home --uid 1000 tailgate \
    && mkdir -p /data \
    && chown -R tailgate:tailgate /data /app

VOLUME ["/data"]
USER tailgate

# OCI metadata. The source label lets GitHub Container Registry link the
# published image back to this repo, which is what Phalanx pulls.
LABEL org.opencontainers.image.source="https://github.com/lsst-so/so-slackbot-evening-tailgate" \
      org.opencontainers.image.description="Vera Rubin Observatory Evening Tailgate Meeting Slack bot" \
      org.opencontainers.image.licenses="GPL-3.0-or-later"

ENTRYPOINT ["tini", "--"]
CMD ["tailgate-bot"]
