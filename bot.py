import requests
import time
from bs4 import BeautifulSoup

BOT_TOKEN = "TOKEN"
CHAT_ID = "CHAT_ID"

URL = "https://fragment.com/gifts?sort=listed&filter=auction"

seen = set()

def send_message(text):
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

while True:
    try:
        html = requests.get(
            URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        ).text

        soup = BeautifulSoup(html, "html.parser")

        gifts = soup.find_all("a")

        for gift in gifts:
            text = gift.get_text(strip=True)

            if text and text not in seen:
                seen.add(text)

                send_message(f"🎁 New Gift:\n{text}")

        time.sleep(30)

    except Exception as e:
        print(e)
        time.sleep(60)
