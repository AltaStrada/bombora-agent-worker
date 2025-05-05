from playwright.sync_api import sync_playwright

def run_bombora(email, password, recipient_email,
                client_url, competitor_url):
    """
    Logs in to Bombora, toggles Summary + Comprehensive, sets recipient,
    clicks 'Generate Report', waits for the XLSX download and returns
    the local file path.
    """

    with sync_playwright() as p:
        # Launch headless Chrome
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

# ── 1.  Sign in ──────────────────────────────────────────────
page.goto("https://login.bombora.com/u/login/identifier")

# wait until the username box is present (up to 60 s)
page.wait_for_selector('#username', timeout=60000)

page.fill('#username', email)                  # type e‑mail
page.click('button[type="submit"]')            # Next / Continue

page.wait_for_selector('input[name="password"]', timeout=60000)
page.fill('input[name="password"]', password)  # type password
page.click('button[type="submit"]')            # Sign in


        # 2 ── Open saved Company‑Surge template
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0")
        page.wait_for_selector("text=Report Output", timeout=15000)

        # 3 ── Ensure both Summary & Comprehensive toggles are ON
        def ensure_toggle(label_text):
            toggle = page.locator(f"text={label_text}")\
                         .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in toggle.get_attribute("class"):
                toggle.click()
        ensure_toggle("Summary")
        ensure_toggle("Comprehensive")

        # 4 ── Fill Report‑Recipients e‑mail
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # 5 ── Generate report and wait for XLSX download
        with page.expect_download(timeout=180000) as dl:
            page.click('button:has-text("Generate Report")')
        xlsx_path = dl.value.path()

        ctx.close(); browser.close()
        return xlsx_path
