# worker.py  – Bombora login + report download (Playwright)
# ----------------------------------------------------------
# • Retries the e-mail “Continue” step up to 3×
# • After every click/Enter it dumps a screenshot and HTML
#   so you can inspect exactly what the bot saw.
# ----------------------------------------------------------

from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPORT_URL = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"


def debug_dump(page, label: str) -> None:
    """Save screenshot + full HTML; logs the paths so Render shows them."""
    img = Path(f"/tmp/{label}.png")
    html = Path(f"/tmp/{label}.html")
    page.screenshot(path=str(img), full_page=True)
    html.write_text(page.content())
    print(f"📸 PW_DUMP {label} :: saved {img.name}")
    print("HTML_DUMP_START")
    print(page.content()[:5000])
    print("HTML_DUMP_END")


def wait_and_fill(page, selector: str, value: str, timeout: int = 60_000):
    """Wait for selector visible, then fill."""
    page.wait_for_selector(selector, timeout=timeout)
    page.fill(selector, value)


def run_bombora(email: str, password: str, recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # 1️⃣ Go to login page
        page.goto("https://login.bombora.com/u/login/identifier")
        debug_dump(page, "login_loaded")

        # fill email
        wait_and_fill(page, "#username", email)

        # now hit Continue up to 3× until the real password field appears
        pw_selector = 'input[name="password"]:not([type="hidden"])'
        for attempt in range(1, 4):
            try:
                page.click('button:has-text("Continue")', timeout=5_000)
            except PWTimeout:
                page.keyboard.press("Enter")
            debug_dump(page, f"after_continue_{attempt}")

            # check for password field
            try:
                page.wait_for_selector(pw_selector, timeout=5_000)
                break
            except PWTimeout:
                continue
        else:
            raise RuntimeError("Password form never appeared")

        # 2️⃣ fill password + submit
        wait_and_fill(page, pw_selector, password)
        page.keyboard.press("Enter")
        debug_dump(page, "after_password")

        # 3️⃣ navigate to the saved report template
        page.goto(REPORT_URL, wait_until="domcontentloaded")
        page.wait_for_selector("text=Report Output", timeout=30_000)

        # 4️⃣ ensure toggles are ON
        def toggle(label: str):
            t = page.locator(f"text={label}") \
                    .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()
        toggle("Summary")
        toggle("Comprehensive")

        # 5️⃣ set recipient and download
        page.fill('input[placeholder*="example.com"]', recipient_email)
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        path = dl.value.path()
        ctx.close()
        browser.close()
        return path
