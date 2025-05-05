FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt && playwright install chromium
ENV PORT=8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
