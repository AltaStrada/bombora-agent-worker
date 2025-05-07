# worker.py  (only the small helper & selector area changed)
# -----------------------------------------------
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import sys, textwrap

REPORT_URL = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"


def debug_dump(page, label: str) -> None:
    """Tiny, flush‑immediate dump that survives Render log truncation."""
    # screenshot for local docker runs
    page.screenshot(path=f"/tmp/{label}.png", full_page=True)
    # 2 000 chars max
    extract = textwrap.shorten(page.content(), 2000, placeholder=" […] ")
    print(f"PW_DUMP>> {label} :: {extract}", flush=True)


def wait_and_fill(page, selector: str, value: str, timeout: int = 60_000):
    page.wait_for_selector(selector, timeout=timeout)
    page.fill(selector, value)


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # 1️⃣  E‑mail step – click Continue up to 4 ×
        page.goto("https://login.bombora.com/u/login/identifier")
        wait_and_fill(page, "#username", email)
        for i in range(4):
            try:
                page.click('button:has-text("Continue")', timeout=4_000)
            except PWTimeout:
                page.keyboard.press("Enter")
            debug_dump(page, f"after_continue_{i+1}")
            # real (visible) password input?
            if page.query_selector('input#password:not([type="hidden"])'):
                break
        else:
            raise RuntimeError("Password form never appeared")

        # 2️⃣  Password
        wait_and_fill(page, 'input#password', password)
        page.keyboard.press("Enter")
        debug_dump(page, "after_password")

        # 3️⃣  Open saved template …
        page.goto(REPORT_URL, wait_until="domcontentloaded")
        page.wait_for_selector("text=Report Output", timeout=30_000)

        # (unchanged rest of the script …)
        # ---------------------------------------------------------------
        # toggle Summary / Comprehensive
        for lbl in ("Summary", "Comprehensive"):
            t = page.locator(f"text={lbl}")\
                    .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()
        # recipient
        page.fill('input[placeholder*="example.com"]', recipient_email)
        # download
        with page.expect_download(timeout=300_000) as dl:
            page.click('button:has-text("Generate Report")')
        xlsx_path = dl.value.path()
        ctx.close(); browser.close()
        return xlsx_path
