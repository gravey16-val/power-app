# Single-stage backend image (Milestone 1). Runs as a non-root user (Render-compatible).
FROM python:3.12-slim

WORKDIR /app

# Create an unprivileged user to run the app.
RUN addgroup --system app && adduser --system --ingroup app app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
