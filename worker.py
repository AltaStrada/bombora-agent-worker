# worker.py  – Bombora login & report download
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPORT_URL  = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"
VISIBLE_PW  = 'input[name="password"]:not(.hide):not([aria-hidden="true"])'   # ✱

def debug_dump(page, label: str):
    img  = Path(f"/tmp/{label}.png")
    page.screenshot(path=str(img), full_page=True)
    print(f"📸 saved {img.name}")
    print(page.content()[:3000])     # first 3k HTML chars

def wait_and_fill(page, sel: str, val: str, t=60_000):
    page.wait_for_selector(sel, timeout=t)
    page.fill(sel, val)

def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx, page = browser.new_context(accept_downloads=True), None
        page = ctx.new_page()

        # 1️⃣ open login & type e‑mail
        page.goto("https://login.bombora.com/u/login/identifier")
        wait_and_fill(page, "#username", email)

        # click Continue up to 3× until visible password box is found
        for i in range(3):
            try:
                page.click('button:has-text("Continue")', timeout=4_000)
            except PWTimeout:
                page.keyboard.press("Enter")
            debug_dump(page, f"after_continue_{i+1}")

            if page.query_selector(VISIBLE_PW):
                break
        else:
            raise RuntimeError("Password form never appeared")

        # 2️⃣ fill password & submit
        wait_and_fill(page, VISIBLE_PW, password)
        page.keyboard.press("Enter")
        debug_dump(page, "after_password")

        # 3️⃣ go to template
        page.goto(REPORT_URL, wait_until="domcontentloaded")
        page.wait_for_selector("text=Report Output", timeout=30_000)

        # ensure toggles
        for label in ("Summary", "Comprehensive"):
            t = page.locator(f"text={label}")\
                   .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()

        # 4️⃣ recipient
        page.fill('input[placeholder*="example.com"]', recipient_email)

        # 5️⃣ run report
        with page.expect_download(timeout=300_000) as dl:
            page.click('button:has-text("Generate Report")')

        return dl.value.path()
