# Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# ── No extra install line needed ──
WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
