import os, io, json, pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from worker import run_bombora
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── 1.  Secrets pulled from Render env‑vars ──────────────────────────────
B_USER = os.getenv("BOMBORA_USER")         # e.g. rajat@sprouts.ai
B_PASS = os.getenv("BOMBORA_PASS")         # plaintext pwd

# Google service‑account JSON is stored as a single env‑var string
SA_JSON = json.loads(os.getenv("GOOGLE_SERVICE_JSON"))

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
CREDS = service_account.Credentials.from_service_account_file(
            "/etc/secrets/service_acct.json", scopes=SCOPES)

# ── 2.  FastAPI schema for POST body ─────────────────────────────────────
class Req(BaseModel):
    requester: str   # e‑mail of sales rep (for reference)
    client:    str   # https://sprouts.ai
    competitor:str   # https://freshworks.com

app = FastAPI()

# ── 3.  Main endpoint ────────────────────────────────────────────────────
@app.post("/")
def handler(req: Req):
    try:
        # 3a. run Playwright routine; returns local XLSX path
        xlsx_path = run_bombora(
            B_USER, B_PASS,
            "bombora-intent-keywords@agent.ai",   # report recipient
            req.client, req.competitor
        )

        # 3b. (OPTIONAL) parse the XLSX later; we just relay Sheet URL
        title = f"{req.client.split('//')[-1]}_Bombora_Intent_Keywords"
        sheets = build("sheets", "v4", credentials=CREDS).spreadsheets()
        ss     = sheets.create(body={"properties": {"title": title}}).execute()
        sheet_url = ss["spreadsheetUrl"]

        return {"status": "ok", "sheetUrl": sheet_url}
    except Exception as e:
        return {"status": "error", "message": str(e)}
