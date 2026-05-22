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

        page.wait_for_timeout(10000)

        # SAYTDAGI BARCHA LINKLARNI OLADI
        links = page.eval_on_selector_all(
            "a",
            "els => els.map(e => e.href)"
        )

        for link in links:

            if "gift" in link.lower():

                gifts.add(link)

        browser.close()

    return gifts

print("Loading existing gifts...")

known = get_gifts()

print("KNOWN:", len(known))

print("Bot started...")

while True:

    try:

        current = get_gifts()

        print("CURRENT:", len(current))

        new_gifts = current - known

        if new_gifts:

            for gift in new_gifts:

                print("NEW:", gift)

                send_message(
                    f"🎁 New Gift!\n\n{gift}"
                )

        known = current

        time.sleep(10)

    except Exception as e:

        print("ERROR:", e)

        time.sleep(20)
