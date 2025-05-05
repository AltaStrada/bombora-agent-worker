# worker.py
# ------------------------------------------------------------------
# Playwright helper for Bombora workflow
# Logs in, toggles Summary + Comprehensive, sets recipient e‑mail,
# runs the Company‑Surge template, waits for XLSX download and
# returns the local file path.
# ------------------------------------------------------------------

from playwright.sync_api import sync_playwright


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    """
    Returns absolute path to downloaded Company‑Surge XLSX
    """

    with sync_playwright() as p:
        # ── Launch headless Chromium ───────────────────────────────
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # ── 1.  Sign‑in screen ────────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier")

        page.wait_for_selector("#username", timeout=60_000)   # e‑mail box
        page.fill("#username", email)
        page.click('button[type="submit"]')

        page.wait_for_selector('input[name="password"]', timeout=60_000)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')

        # ── 2.  Open saved Company‑Surge template ────────────────
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0")
        page.wait_for_selector("text=Report Output", timeout=15_000)

        # ── 3.  Ensure Summary & Comprehensive toggles are ON ────
        def ensure_toggle(label: str) -> None:
            toggle = page.locator(f"text={label}") \
                        .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (toggle.get_attribute("class") or ""):
                toggle.click()

        ensure_toggle("Summary")
        ensure_toggle("Comprehensive")

        # ── 4.  Fill Report‑Recipients field ─────────────────────
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # ── 5.  Generate report & await download ─────────────────
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()

        ctx.close()
        browser.close()
        return xlsx_path
