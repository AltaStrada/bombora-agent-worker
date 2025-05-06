# worker.py -----------------------------------------------------------
from pathlib import Path
from playwright.sync_api import sync_playwright


def run_bombora(email: str,
                password: str,
                recipient_email: str,
                client_url: str,
                competitor_url: str) -> str:
    """
    Log in to Bombora, run the pre‑saved Company–Surge template,
    wait for XLSX download, return the local file path.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # ── 1 ▸ LOGIN ─────────────────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier")
        page.wait_for_selector("#username", timeout=60_000)
        page.fill("#username", email)
        page.press("#username", "Enter")     # show password box

        page.wait_for_selector("#password", timeout=60_000)
        page.fill("#password", password)
        page.press("#password", "Enter")     # submit form

        # ── 2 ▸ OPEN SAVED TEMPLATE ──────────────────────────────
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0")
        page.wait_for_selector("text=Report Output", timeout=15_000)

        # ── 3 ▸ TOGGLE SUMMARY & COMPREHENSIVE ON ────────────────
        def ensure_toggle(label: str):
            toggle = page.locator(f"text={label}")\
                         .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (toggle.get_attribute("class") or ""):
                toggle.click()

        ensure_toggle("Summary")
        ensure_toggle("Comprehensive")

        # ── 4 ▸ SET RECIPIENT ────────────────────────────────────
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # ── 5 ▸ GENERATE & DOWNLOAD REPORT ───────────────────────
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()

        ctx.close()
        browser.close()
        return xlsx_path
