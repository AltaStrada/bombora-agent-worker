# worker.py  – Bombora login + report download
# --------------------------------------------
# * First thing it does is hit the login URL, wait until
#   the page is fully loaded, then logs a PW_DUMP line that
#   will ALWAYS appear in Render → Application logs.
# * All later dumps use the same logger, so every HTML
#   snippet is guaranteed to reach the log stream.
# --------------------------------------------

from pathlib import Path
import logging, textwrap
from typing import Optional
from playwright.sync_api import (
    sync_playwright, TimeoutError as PWTimeout
)

# ── basic logger (visible in Render “Application” log) ────────────
log = logging.getLogger("pw")
log.setLevel(logging.INFO)

def debug_dump(page, label: str, max_len: int = 2000) -> None:
    """Emit one‑liner with partial HTML so we can see what Playwright sees."""
    snippet = textwrap.shorten(page.content(), max_len, placeholder=" […] ")
    log.info("PW_DUMP %s :: %s", label, snippet)


REPORT_URL = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"


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

        # 1️⃣  Go to login → wait for full load
        page.goto("https://login.bombora.com/u/login/identifier",
                  wait_until="load")
        debug_dump(page, "login_loaded")          # <– always shows up

        # 2️⃣  Fill e‑mail, then loop Click/Enter until password box visible
        wait_and_fill(page, "#username", email)

        pw_selector: Optional[str] = None
        for attempt in range(1, 4):
            try:
                page.click('button:has-text("Continue")', timeout=5_000)
            except PWTimeout:
                page.keyboard.press("Enter")

            debug_dump(page, f"after_continue_{attempt}")

            try:
                page.wait_for_selector('input[name="password"]:not([type="hidden"])',
                                       timeout=5_000)
                pw_selector = "#password"
                break
            except PWTimeout:
                continue

        if pw_selector is None:
            raise RuntimeError("Password form never appeared")

        # 3️⃣  Fill password & submit
        wait_and_fill(page, pw_selector, password)
        page.keyboard.press("Enter")
        debug_dump(page, "after_password")

        # 4️⃣  Open saved Company‑Surge template
        page.goto(REPORT_URL, wait_until="domcontentloaded")
        page.wait_for_selector("text=Report Output", timeout=30_000)
        debug_dump(page, "template_loaded")

        # Ensure Summary + Comprehensive toggles are ON
        def toggle(label: str):
            t = page.locator(f"text={label}")\
                    .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()
        toggle("Summary")
        toggle("Comprehensive")

        # 5️⃣  Recipient e‑mail
        page.fill('input[placeholder*="example.com"]', recipient_email)

        # 6️⃣  Generate report → wait for download
        with page.expect_download(timeout=300_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close()
        browser.close()
        return xlsx_path
