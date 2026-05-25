import asyncio
import os
from playwright.async_api import async_playwright
from telegram import Bot

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]
URL = "https://marketapp.ws/gifts/?tab=nfts&sort_by=recently_touch&filter_by=auction_no_bids"

async def main():
    bot = Bot(token=BOT_TOKEN)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        page = await browser.new_page(user_agent="Mozilla/5.0 Chrome/124.0.0.0 Safari/537.36")
        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(6)

        html = await page.evaluate("""() => {
            const card = document.querySelector('.js-grid-card[data-nft-address]');
            return card ? card.outerHTML : 'Topilmadi';
        }""")

        msg = f"*1 ta kartaning HTML:*\n```\n{html[:3500]}\n```"
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

if __name__ == "__main__":
    asyncio.run(main())
