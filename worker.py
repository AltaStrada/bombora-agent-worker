# worker.py  – Bombora login + report download (Playwright)
# -----------------------------------------------
# • Retries the e‑mail “Continue” step up to 3×
# • After every click/Enter it dumps a screenshot and first 5 000 chars
#   of the page’s HTML to /tmp and to stdout so you can inspect logs.
# -----------------------------------------------

from pathlib import Path
from typing   import Optional
from playwright.sync_api import (
    sync_playwright, TimeoutError as PWTimeout
)

REPORT_URL = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"


def debug_dump(page, label: str) -> None:
    """Save screenshot + partial HTML; path printed so Render logs show it."""
    img = Path(f"/tmp/{label}.png")
    html = Path(f"/tmp/{label}.html")
    page.screenshot(path=str(img), full_page=True)
    html.write_text(page.content())
    print(f"📸 saved {img.name}")
    print("HTML_DUMP_START")
    print(page.content()[:5000])
    print("HTML_DUMP_END")


def wait_and_fill(page, selector: str, value: str, timeout: int = 60_000):
    page.wait_for_selector(selector, timeout=timeout)
    page.fill(selector, value)


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    """
    Logs into Bombora, runs saved Company‑Surge template,
    waits for XLSX download and returns the local filepath.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # 1️⃣  Go to login
        page.goto("https://login.bombora.com/u/login/identifier")

        # ── Put e‑mail, then repeatedly press Continue / Enter until
        #    the password field appears (max 3 tries) ───────────────
        wait_and_fill(page, "#username", email)

        pw_box: Optional[str] = None
        for attempt in range(1, 4):
            # Click Continue (or press Enter)
            try:
                page.click('button:has-text("Continue")', timeout=5_000)
            except PWTimeout:
                page.keyboard.press("Enter")

            debug_dump(page, f"after_continue_{attempt}")

            # try to locate the real password input (not hidden)
            try:
                pw_box = page.wait_for_selector(
                    'input[name="password"]:not([type="hidden"])',
                    timeout=5_000
                ).locator("#password").selector
                break  # got it
            except PWTimeout:
                continue

        if pw_box is None:
            raise RuntimeError("Password form never appeared")

        # 2️⃣  Fill password & submit
        wait_and_fill(page, pw_box, password)
        page.keyboard.press("Enter")
        debug_dump(page, "after_password")

        # 3️⃣  Navigate to saved template
        page.goto(REPORT_URL, wait_until="domcontentloaded")
        page.wait_for_selector("text=Report Output", timeout=30_000)

        # Ensure Summary + Comprehensive toggles are ON
        def toggle(label: str):
            t = page.locator(f"text={label}")\
                    .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()

        toggle("Summary")
        toggle("Comprehensive")

        # 4️⃣  Recipient e‑mail
        page.fill('input[placeholder*="example.com"]', recipient_email)

        # 5️⃣  Generate report → wait for download
        with page.expect_download(timeout=300_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close()
        browser.close()
        return xlsx_path
