# worker.py  ── minimal, bullet‑proof login --------------------------
from pathlib import Path
from playwright.sync_api import sync_playwright


def run_bombora(email: str,
                password: str,
                recipient: str,
                client_url: str,
                competitor_url: str) -> str:

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        # ── 1 ▸ E‑mail screen ────────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier",
                  wait_until="domcontentloaded")

        page.fill("#username", email)
        page.click("button[type='submit']")                # first Continue

        # ▸ 1a  Wait for either a new URL OR an iframe to load
        page.wait_for_load_state("networkidle")
        if "/password" in page.url:
            pw_root = page     # password is in the main doc
        else:
            # Try the first visible iframe that contains ‘password’
            try:
                iframe = page.frame_locator("iframe").locator(
                    "input[name='password']").frame
                pw_root = iframe.page
            except Exception:
                raise RuntimeError("Password form not found")

        # ── 2 ▸ Password screen ────────────────────────────────
        pw_root.fill("input[name='password']", password)
        pw_root.click("button[type='submit']")             # second Continue
        page.wait_for_load_state("networkidle")

        # ── 3 ▸ Saved Company‑Surge template ───────────────────
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0")
        page.wait_for_selector("text=Report Output", timeout=15_000)

        for label in ("Summary", "Comprehensive"):
            tg = page.locator(f"text={label}")\
                    .locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (tg.get_attribute("class") or ""):
                tg.click()

        page.fill('input[placeholder*="example.com"]', recipient)

        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')

        xlsx_path = dl.value.path()
        ctx.close(); browser.close()
        return xlsx_path
