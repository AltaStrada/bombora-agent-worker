# worker.py  ▸ robust Bombora login
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

def run_bombora(email: str, password: str,
                recipient_email: str,
                client_url: str, competitor_url: str) -> str:
    """
    Logs in to Bombora, runs saved Company‑Surge template,
    downloads XLSX, returns local file path.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(accept_downloads=True)
        page    = ctx.new_page()

        # ── 1. open ID page ──────────────────────────────────────
        page.goto("https://login.bombora.com/u/login/identifier")

        # type e‑mail, press Enter to reveal pw box
        page.fill("#username", email)
        page.keyboard.press("Enter")

        # robust wait: field must be **attached & enabled**
        for _ in range(120):            # up to ~12 s
            try:
                pw = page.query_selector("#password")
                if pw and pw.is_enabled():
                    break
            except Exception:
                pass
            page.wait_for_timeout(100)   # 0.1 s
        else:
            raise RuntimeError("Password form not found")

        # enter password & submit (Enter key)
        page.fill("#password", password)
        page.keyboard.press("Enter")

        # ── 2.  open saved template ─────────────────────────────
        page.wait_for_load_state("networkidle", timeout=30_000)
        page.goto("https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0",
                  timeout=60_000)
        page.wait_for_selector("text=Report Output", timeout=30_000)

        # ── 3. ensure Summary & Comprehensive toggles ON ───────
        def ensure(label: str):
            t = page.locator(f"text={label}").locator("xpath=../..//div[contains(@class,'toggle')]")
            if "off" in (t.get_attribute("class") or ""):
                t.click()
        ensure("Summary")
        ensure("Comprehensive")

        # ── 4. set recipient ───────────────────────────────────
        page.fill('input[placeholder="name@example.com"]', recipient_email)

        # ── 5. generate & download ─────────────────────────────
        with page.expect_download(timeout=180_000) as dl:
            page.click('button:has-text("Generate Report")')
        xlsx_path: Path = dl.value.path()

        ctx.close(); browser.close()
        return str(xlsx_path)
