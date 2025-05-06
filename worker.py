# worker.py
# ------------------------------------------------------------------
# Playwright helper for Bombora workflow
# • Login workflow that mirrors Bombora’s exact UX:
#     1.  Type e‑mail in #username  →  press Enter
#     2.  Password field appears   →  type password  →  press Enter
# • Opens saved Company‑Surge template, toggles Summary & Comprehensive
# • Sends report to recipient, waits for XLSX download, returns its path
# ------------------------------------------------------------------

from playwright.sync_api import sync_playwright


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    """
    Logs into Bombora, runs Company‑Surge template, downloads XLSX,
    returns the absolute file path.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # ── 1.  Go to login page ────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier")

        # 1a. Fill e‑mail, hit Enter (Bombora reveals password field)
        page.wait_for_selector("#username", timeout=60_000)
        page.fill("#username", email)
        page.press("#username", "Enter")

        # 1b. Wait for visible password input, fill, press Enter
        pwd_sel = 'input[type="password"]:not(.hide):not([aria-hidden="true"])'
        page.wait_for_selector(pwd_sel, timeout=60_000)
        page.fill(pwd_sel, password)
        page.press(pwd_sel, "Enter")

        # ── 2.  Open saved Company‑Surge template ───────────────
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0")
        page.wait_for_selector("text=Report Output", timeout=15_000)

        # 3.  Ensure Summary & Comprehensive toggles are ON
        def ensure_toggle(label: str):
            toggle = (
                page.locator(f"text={label}")
                .locator("xpath=../..//div[contains(@class,'toggle')]")
            )
            if "off" in (toggle.get_attribute("class") or ""):
                toggle.click()

        ensure_toggle("Summary")
        ensure_toggle("Comprehensive")

        # 4.  Fill report‑recipient e‑mail
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # 5.  Generate report and wait for XLSX download (≤3 min)
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close(); browser.close()
        return xlsx_path
