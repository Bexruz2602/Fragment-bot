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

    gifts = set()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        page.goto(URL, timeout=60000)

        page.wait_for_timeout(8000)

        cards = page.locator("body").inner_text()

        browser.close()

        return cards

print("Loading...")

old = get_gifts()

print("Bot started...")

while True:

    try:

        current = get_gifts()

        if current != old:

            send_message(
                "🎁 Yangi gift yoki auction paydo bo'ldi!"
            )

            print("NEW CHANGE")

            old = current

        time.sleep(15)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(30)
