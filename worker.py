# worker.py  ─────────────────────────────────────────────────────────────
# Playwright helper for Bombora → downloads Company‑Surge XLSX
# -----------------------------------------------------------------------
from pathlib import Path
from time import sleep
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def run_bombora(email: str,
                pwd: str,
                recipient_email: str,
                client_url: str,
                competitor_url: str) -> str:
    """Logs in, triggers saved Company‑Surge template, waits for XLSX,
    returns local file‑path."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # 1️⃣  OPEN LOGIN PAGE -------------------------------------------------
        page.goto("https://login.bombora.com/u/login/identifier",
                  wait_until="domcontentloaded")

        # 2️⃣  ENTER E‑MAIL + FIGHT THE DOUBLE‑CLICK --------------------------
        page.fill("input[name='username']", email)

        # Try Continue (or Enter) up to 3× until password field shows
        for attempt in range(3):
            page.keyboard.press("Enter")              # quickest
            try:
                page.wait_for_selector("input[name='password']",
                                       timeout=3_000)
                break                                 # success
            except PWTimeout:
                # maybe Bombora needs the visible button click…
                try:
                    page.click("button:has-text('Continue')",
                               timeout=1_000)
                except PWTimeout:
                    pass
                sleep(1)                              # tiny grace pause
        else:
            raise RuntimeError("Password form never appeared")

        # 3️⃣  ENTER PASSWORD & SUBMIT ----------------------------------------
        page.fill("input[name='password']", pwd)
        # Bombora accepts Enter; keep a back‑up click just in case
        page.keyboard.press("Enter")
        sleep(1)
        try:
            page.click("button:has-text('Continue')", timeout=1_500)
        except PWTimeout:
            pass                                      # fine if button gone

        # 4️⃣  OPEN SAVED COMPANY‑SURGE TEMPLATE ------------------------------
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0",
                  wait_until="networkidle")

        # Wait until the “Report Output” tab is present
        page.wait_for_selector("text=Report Output", timeout=15_000)

        # 5️⃣  ENSURE SUMMARY & COMPREHENSIVE TOGGLES ON ----------------------
        def ensure_toggle(label: str):
            tog = page.locator(f"text={label}") \
                      .locator("xpath=../..//div[contains(@class,'toggle')]")
            cls = tog.get_attribute("class") or ""
            if "off" in cls:
                tog.click()
                sleep(0.2)

        ensure_toggle("Summary")
        ensure_toggle("Comprehensive")

        # 6️⃣  SET RECIPIENT & RUN REPORT ------------------------------------
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        with page.expect_download(timeout=180_000) as dl_info:
            page.click("button:has-text('Generate Report')")

        xlsx_file: Path = dl_info.value.path()         # local temp file

        ctx.close()
        browser.close()
        return str(xlsx_file)
