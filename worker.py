# ── 1. Login ──────────────────────────────────────────────
page.goto("https://login.bombora.com/u/login/identifier")

# 1a. Fill email
page.wait_for_selector("#username", timeout=60_000)
page.fill("#username", email)

# 1b. Press Enter and wait either for navigation or for Password label
with page.expect_any_event("framenavigated", timeout=10_000) as nav:
    page.press("#username", "Enter")
try:
    nav.value   # navigation happened
except TimeoutError:
    # If no nav, wait for password elements to appear
    page.wait_for_selector("label:has-text('Password'), input[type='password']", timeout=10_000)

# 1c. Now fill password and submit with Enter
pwd_sel = 'input[type="password"]:not(.hide):not([aria-hidden="true"])'
page.wait_for_selector(pwd_sel, timeout=30_000)
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
