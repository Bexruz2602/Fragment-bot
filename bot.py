from playwright.sync_api import sync_playwright
import requests
import time
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://marketapp.ws/gifts/?tab=nfts&sort_by=recently_touch&filter_by=auction_no_bids"

known = set()

def send_message(text):
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

def get_gifts():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        page.goto(URL, timeout=60000)

        page.wait_for_timeout(8000)

        html = page.content()

        browser.close()

        return html

print("Loading...")

old_html = get_gifts()

print("Bot started")

while True:

    try:

        new_html = get_gifts()

        if new_html != old_html:

            send_message(
                "🎁 MarketApp gifts sahifasida o'zgarish bo'ldi!"
            )

            print("CHANGE DETECTED")

            old_html = new_html

        time.sleep(5)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(15)
