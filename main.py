import requests
import time
import os
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://marketapp.ws/gifts/?tab=nfts&sort_by=recently_touch&filter_by=auction_no_bids"

known = set()

headers = {
    "User-Agent": "Mozilla/5.0"
}

def send_message(text):
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

def get_gifts():
    html = requests.get(URL, headers=headers).text

    soup = BeautifulSoup(html, "html.parser")

    gifts = set()

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/gifts/" in href or "/gift/" in href:
            gifts.add(href)

    return gifts

# Birinchi yuklashda eski giftlarni eslab qoladi
known = get_gifts()

print("Bot started...")

while True:
    try:
        current = get_gifts()

        new_gifts = current - known

        for gift in new_gifts:

            full_link = f"https://marketapp.ws{gift}"

            print("NEW:", full_link)

            send_message(
                f"🎁 New NFT Gift!\n\n{full_link}"
            )

        known = current

        time.sleep(5)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(15)
