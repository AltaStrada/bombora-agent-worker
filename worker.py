# worker.py  – Bombora login + report download (Playwright)
# ----------------------------------------------------------
# • Submits your username with two ENTERs
# • Waits by #password (no hidden‐input gymnastics)
# • Debug‐dumps immediately after email and after password
# • Fails fast if Report Output never becomes visible
# ----------------------------------------------------------

from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPORT_URL = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"


def debug_dump(page, label: str) -> None:
    """Save screenshot + partial HTML; flush prints so Render logs show them immediately."""
    img = Path(f"/tmp/{label}.png")
    html = Path(f"/tmp/{label}.html")
    page.screenshot(path=str(img), full_page=True)
    html.write_text(page.content())
    print(f"📸 PW_DUMP {label} :: saved {img.name}", flush=True)
    print("HTML_DUMP_START", flush=True)
    print(page.content()[:5000], flush=True)
    print("HTML_DUMP_END", flush=True)


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # 1️⃣  Go to login page & dump
        page.goto("https://login.bombora.com/u/login/identifier")
        debug_dump(page, "login_loaded")

        # 2️⃣  Fill username, press ENTER twice
        page.fill("#username", email)
        page.keyboard.press("Enter")
        page.keyboard.press("Enter")
        debug_dump(page, "after_email_enter")

        # 3️⃣  Wait for the real password field
        try:
            page.wait_for_selector("input#password", timeout=60_000)
        except PWTimeout:
            debug_dump(page, "password_field_missing")
            raise RuntimeError("Password form never appeared")

        # 4️⃣  Fill password & submit
        page.fill("input#password", password)
        page.keyboard.press("Enter")
        debug_dump(page, "after_password_enter")

        # 5️⃣  Navigate to report page & wait for Report Output
        page.goto(REPORT_URL, wait_until="networkidle")
        try:
            page.wait_for_selector("div.section-title:has-text('Report Output')", timeout=60_000)
        except PWTimeout:
            debug_dump(page, "report_page_failed")
            raise RuntimeError("Report Output never became visible")

        # 6️⃣  Ensure Summary + Comprehensive toggles are ON
        def toggle(label: str):
            t = page.locator(f"text={label}") \
                    .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()
        toggle("Summary")
        toggle("Comprehensive")

        # 7️⃣  Fill recipient + download
        page.fill('input[placeholder*="example.com"]', recipient_email)
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close(); browser.close()
        return xlsx_path
