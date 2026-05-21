import os
import time
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = "TOKEN"
CHAT_ID = "CHAT_ID"

URL = "https://fragment.com/gifts?sort=listed&filter=auction"

seen = set()

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

def get_gifts():
    gifts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        page.goto(URL, timeout=60000)

        page.wait_for_timeout(7000)

        html = page.content()

        print(html[:500])

        links = page.query_selector_all("a")

        for l in links:
            try:
                text = l.inner_text().strip()

                if text and len(text) > 5:
                    gifts.append(text)

            except:
                pass

        browser.close()

    return gifts

send("✅ BOT STARTED")

while True:
    try:
        gifts = get_gifts()

        print(gifts[:10])

        for g in gifts:

            if g not in seen:
                seen.add(g)

                send(f"🎁 NEW GIFT:\n{g}")

        print("checked")

    except Exception as e:
        print("ERROR:", e)

    time.sleep(20)
