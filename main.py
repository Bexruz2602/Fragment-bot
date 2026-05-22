import requests
import time
import os
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://fragment.com/gifts?sort=listed&filter=auction"

known_gifts = set()

def send_message(text):
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

def get_gifts():
    html = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    ).text

    soup = BeautifulSoup(html, "html.parser")

    gifts = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/gift/" in href:
            gifts.add(href)

    return gifts

# FIRST LOAD
known_gifts = get_gifts()

print("Bot started...")

while True:
    try:
        current_gifts = get_gifts()

        new_gifts = current_gifts - known_gifts

        for gift in new_gifts:
            link = f"https://fragment.com{gift}"

            send_message(
                f"🎁 New Auction Gift!\n\n{link}"
            )

            print("NEW:", link)

        known_gifts = current_gifts

        time.sleep(15)

    except Exception as e:
        print(e)
        time.sleep(30)
