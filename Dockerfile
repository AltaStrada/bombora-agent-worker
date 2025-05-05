# --- Dockerfile ---
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt   # installs FastAPI, pandas, etc.

ENV PORT=8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
