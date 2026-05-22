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

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto(URL, timeout=60000)

        page.wait_for_timeout(5000)

        links = page.locator("a").evaluate_all(
            "(elements) => elements.map(e => e.href)"
        )

        for link in links:

            if "/gift/" in link or "/gifts/" in link:
                gifts.add(link)

        browser.close()

    return gifts

print("Loading existing gifts...")

known = get_gifts()

print("Bot started...")

while True:
    try:

        current = get_gifts()

        new_gifts = current - known

        for gift in new_gifts:

            print("NEW:", gift)

            send_message(
                f"🎁 New NFT Gift!\n\n{gift}"
            )

        known = current

        time.sleep(5)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(15)
