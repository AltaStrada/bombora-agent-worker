import os, pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from worker import run_bombora
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── 1. Bombora credentials from Render env‑vars ──────────────────────────
B_USER = os.getenv("BOMBORA_USER")      # e.g. rajat@sprouts.ai
B_PASS = os.getenv("BOMBORA_PASS")      # plaintext password

# ── 2. Google service‑account loaded from Secret File ────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
CREDS = service_account.Credentials.from_service_account_file(
            "/etc/secrets/service_acct.json", scopes=SCOPES)

# ── 3. FastAPI request schema ────────────────────────────────────────────
class Req(BaseModel):
    requester:  str   # sales‑rep e‑mail
    client:     str   # https://sprouts.ai
    competitor: str   # https://freshworks.com

app = FastAPI()

# ── 4. Main endpoint ─────────────────────────────────────────────────────
@app.post("/")
def handler(req: Req):
    try:
        # 4a. run Playwright helper; returns XLSX path
        xlsx_path = run_bombora(
            B_USER,
            B_PASS,
            "bombora-intent-keywords@agent.ai",   # Bombora report recipient
            req.client,
            req.competitor,
        )

        # 4b. Create an empty Google Sheet (we’ll fill later if needed)
        title = f"{req.client.split('//')[-1]}_Bombora_Intent_Keywords"
        sheets_api = build("sheets", "v4", credentials=CREDS).spreadsheets()
        ss = sheets_api.create(body={"properties": {"title": title}}).execute()
        sheet_url = ss["spreadsheetUrl"]

        return {"status": "ok", "sheetUrl": sheet_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}
