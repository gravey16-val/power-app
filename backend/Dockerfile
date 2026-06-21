FROM python:3.12-slim

WORKDIR /app

# Non-root user (required by Render).
RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
