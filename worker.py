# worker.py
# ------------------------------------------------------------------
# Playwright helper for Bombora workflow
# 1. Logs in (username ▸ Continue ▸ password ▸ Continue)
#    – skips the hidden password input by filtering .hide / aria‑hidden
# 2. Opens saved Company‑Surge template, toggles Summary + Comprehensive
# 3. Sets report recipient, generates report, waits for XLSX download
# 4. Returns the downloaded file path
# ------------------------------------------------------------------

from playwright.sync_api import sync_playwright


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # ── 1. Login (two‑step) ─────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier")

        # 1a. Username ▸ Continue
        page.wait_for_selector("#username", timeout=60_000)
        page.fill("#username", email)
        page.click('button:has-text("Continue")')

        # 1b. Visible password input (ignore hidden placeholder)
        pwd_selector = 'input[type="password"]:not(.hide):not([aria-hidden="true"])'
        page.wait_for_selector(pwd_selector, timeout=60_000)
        page.locator(pwd_selector).fill(password)
        page.click('button:has-text("Continue")')

        # ── 2. Open saved Company‑Surge template ───────────────
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0")
        page.wait_for_selector("text=Report Output", timeout=15_000)

        # 3. Ensure Summary & Comprehensive toggles are ON
        def ensure_toggle(label: str):
            toggle = (
                page.locator(f"text={label}")
                .locator("xpath=../..//div[contains(@class,'toggle')]")
            )
            if "off" in (toggle.get_attribute("class") or ""):
                toggle.click()

        ensure_toggle("Summary")
        ensure_toggle("Comprehensive")

        # 4. Fill report recipient e‑mail
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # 5. Generate report and wait for XLSX download
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close(); browser.close()
        return xlsx_path
