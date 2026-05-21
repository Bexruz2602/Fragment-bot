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
        data={"chat_id": CHAT_ID, "text": text}
    )

def get_gifts():
    gifts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_timeout(5000)

        items = page.query_selector_all("a")

        for i in items:
            t = i.inner_text().strip()
            if t:
                gifts.append(t)

        browser.close()

    return gifts

while True:
    try:
        gifts = get_gifts()

        for g in gifts:
            if g not in seen:
                seen.add(g)
                send("🎁 NEW GIFT:\n" + g)

        print("checked")

    except Exception as e:
        print(e)

    time.sleep(10)
