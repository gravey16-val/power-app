# Single-stage image (project rule: no multi-stage builds).
# Base image pinned to a patch version for reproducible builds (reviewer feedback).
FROM python:3.12.7-slim

WORKDIR /app

# Non-root user is required by Render.
RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Read $PORT so the same image works on Render (which injects its own PORT)
# and locally (defaults to 8000). No --reload in this CMD (production-safe).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
