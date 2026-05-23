import asyncio
import os
import logging
from playwright.async_api import async_playwright
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]

URL = (
    "https://marketapp.ws/gifts/"
    "?tab=nfts&sort_by=recently_touch&filter_by=auction_no_bids"
)


async def main():
    bot = Bot(token=BOT_TOKEN)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(8)

        result = await page.evaluate("""() => {
            // #12345 ko'rinishidagi gift nomlarini qidirish
            const allLinks = Array.from(document.querySelectorAll('a'));
            const giftLinks = allLinks.filter(a => {
                const text = a.innerText || '';
                const href = a.getAttribute('href') || '';
                return text.match(/#\d{3,}/) || href.match(/gift|nft|item/i);
            });

            if (giftLinks.length > 0) {
                return {
                    found: giftLinks.length,
                    samples: giftLinks.slice(0, 2).map(a => ({
                        href: a.getAttribute('href'),
                        text: (a.innerText || '').substring(0, 80),
                        outerHTML: a.outerHTML.substring(0, 400)
                    }))
                };
            }

            // Hech narsa topilmasa — sahifaning birinchi 3000 belgisini yuborish
            return {
                found: 0,
                bodyStart: document.body.innerHTML.substring(0, 3000)
            };
        }""")

        if result.get("found", 0) > 0:
            msg = f"✅ *{result['found']} ta gift linki topildi!*\n\n"
            for i, s in enumerate(result.get("samples", []), 1):
                msg += f"*{i}. href:* `{s['href']}`\n"
                msg += f"*text:* `{s['text']}`\n"
                msg += f"*html:*\n```\n{s['outerHTML'][:300]}\n```\n\n"
        else:
            body = result.get("bodyStart", "")
            msg = f"⚠️ Gift linki topilmadi\n\n*HTML boshi:*\n```\n{body[:2000]}\n```"

        # Telegram 4096 belgidan uzun qabul qilmaydi
        if len(msg) > 4000:
            msg = msg[:4000] + "\n...(qisqartirildi)"

        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")


if __name__ == "__main__":
    asyncio.run(main())
