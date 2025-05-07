# worker.py  – Bombora login + Company‑Surge download
# --------------------------------------------------
# ✔ waits for URL change to “…/password”
# ✔ retries the Continue click / Enter up to 3×
# ✔ dumps screenshot + HTML after each attempt
# --------------------------------------------------

from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPORT_URL = "https://surge.bombora.com/Surge/Manage?a=88411#/Edit/0"


def dump(page, tag: str) -> None:
  img  = Path(f"/tmp/{tag}.png")
  html = Path(f"/tmp/{tag}.html")
  page.screenshot(path=str(img), full_page=True)
  html.write_text(page.content())
  print(f"📸 {img.name} / {html.name}")


def run_bombora(email: str, password: str, recipient: str,
                client_url: str, competitor_url: str) -> str:

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx     = browser.new_context(accept_downloads=True)
    page    = ctx.new_page()

    # 1️⃣  open login page
    page.goto("https://login.bombora.com/u/login/identifier",
              wait_until="domcontentloaded")

    # E‑mail
    page.fill("#username", email)

    pw_visible: bool = False
    for attempt in range(1, 4):
      # click Continue (fallback to Enter if button missing)
      try:
        page.click('button:has-text("Continue")', timeout=4_000)
      except PWTimeout:
        page.keyboard.press("Enter")

      # Wait for location to contain “…/password” (up to 10 s)
      try:
        page.wait_for_url("**/password", timeout=10_000)
      except PWTimeout:
        pass  # user might already be on /password

      # Wait up to 6 s for a *visible* password box
      try:
        page.wait_for_selector('#password:visible', timeout=6_000)
        pw_visible = True
        dump(page, f"password_ready_{attempt}")
        break
      except PWTimeout:
        dump(page, f"after_continue_{attempt}")
        continue

    if not pw_visible:
      raise RuntimeError("Password form never appeared")

    # 2️⃣  fill password & submit
    page.fill('#password', password)
    page.keyboard.press("Enter")
    dump(page, "after_submit_pwd")

    # 3️⃣  open saved Company‑Surge template
    page.goto(REPORT_URL, wait_until="domcontentloaded")
    page.wait_for_selector("text=Report Output", timeout=30_000)

    # ensure Summary & Comprehensive toggles ON
    def ensure(label: str):
      t = page.locator(f"text={label}") \
              .locator("xpath=../..//div[contains(@class,'toggle')]")
      if "off" in (t.get_attribute("class") or ""):
        t.click()

    ensure("Summary")
    ensure("Comprehensive")

    # 4️⃣  recipient e‑mail
    page.fill('input[placeholder*="example.com"]', recipient)

    # 5️⃣  run report → await download
    with page.expect_download(timeout=300_000) as dl:
      page.click('button:has-text("Generate Report")')

    xlsx = dl.value.path()
    ctx.close()
    browser.close()
    return xlsx
