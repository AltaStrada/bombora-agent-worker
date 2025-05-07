# Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# ↓ ONE extra line – installs only Chromium once during build
RUN playwright install chromium

WORKDIR /app
COPY . .

# install Python deps
RUN pip install -r requirements.txt

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
