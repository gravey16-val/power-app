# Single-stage image (no multi-stage builds — project convention).
# Base image pinned to a patch version for reproducible builds
# (past review: bare "3.12-slim" lets each redeploy pull a different image).
FROM python:3.12.8-slim

WORKDIR /app

# Non-root user "app" — required by Render.
RUN addgroup --system app && adduser --system --ingroup app app

# Install runtime + test deps in this single stage.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Bind to $PORT when provided (Render injects it); default 8000 for local/compose.
# (Past review: never hardcode --port 8000 — Render routes to $PORT.)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
