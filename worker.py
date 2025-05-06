# worker.py
# ------------------------------------------------------------------
# Playwright helper for Bombora workflow
# • Two‑step login (username ▸ Continue ▸ password ▸ Continue)
# • Debug: saves screenshot & partial DOM after first Continue
# • Uses label‑based selector to target visible password field
# • Generates Company‑Surge report, waits for XLSX, returns its path
# ------------------------------------------------------------------

from playwright.sync_api import sync_playwright


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # ── 1. Login ────────────────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier")

        # 1a. Username ▸ Continue
        page.wait_for_selector("#username", timeout=60_000)
        page.fill("#username", email)
        page.click('button:has-text("Continue")')

        # 🔍 DEBUG: snapshot & DOM after username step
        page.screenshot(path="/tmp/after_continue.png", full_page=True)
        print("📸 saved after_continue.png")
        print("DOM snippet:",
              page.inner_html("body")[:1000].replace("\n", " ")[:1000])

        # 1b. Locate password field by label, fill, Continue
        pwd_locator = page.locator("label:has-text('Password')").locator("input")
        pwd_locator.wait_for(state="visible", timeout=60_000)
        pwd_locator.fill(password)
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

        # 4. Fill report recipient
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # 5. Generate report & await XLSX download
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close(); browser.close()
        return xlsx_path
