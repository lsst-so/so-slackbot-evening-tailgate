FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py config.py state.py messages.py jobs.py scheduler.py ./

# The SQLite state file defaults to a path under /data so it survives
# container restarts/upgrades when /data is a mounted volume.
ENV TAILGATE_DB_PATH=/data/tailgate_state.db

RUN useradd --system --create-home --uid 1000 tailgate \
    && mkdir -p /data \
    && chown -R tailgate:tailgate /data /app

VOLUME ["/data"]
USER tailgate

CMD ["python", "app.py"]
