# Backend — Weather Dashboard API
# Single-stage build (NO multi-stage). Runs as the non-root user `appuser`.
FROM python:3.12-slim

# Don't write .pyc files; flush stdout/stderr immediately so logs stream to Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root system user/group up front (required by Render).
RUN groupadd --system appuser \
 && useradd --system --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

# Install Python dependencies as root into system site-packages.
# Includes pytest + httpx so `docker compose exec backend pytest` works in-container.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy application source (main.py, database.py, models.py, routers/, tests/, ...).
COPY . .

# Hand ownership to the non-root user, then drop privileges for runtime.
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Production command — NO --reload.
# DATABASE_URL is read from the environment at runtime (see database.py / docker-compose.yml).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
