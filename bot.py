import asyncio
import os
import logging
from playwright.async_api import async_playwright
from telegram import Bot

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
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

        marketapp_requests = []

        # Faqat marketapp.ws ga ketgan SO'ROVLAR
        async def on_request(request):
            if "marketapp.ws" in request.url:
                line = f"{request.method} {request.url}"
                marketapp_requests.append(line)
                logger.info(f"REQ: {line}")

        page.on("request", on_request)

        await bot.send_message(chat_id=CHAT_ID, text="⏳ Sahifa yuklanmoqda...")

        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(8)

        # Sahifa HTML si bor yoqligini tekshirish
        html_len = await page.evaluate("document.body.innerHTML.length")
        title    = await page.title()

        # Natijani yuborish
        if marketapp_requests:
            msg = f"📡 *marketapp.ws ga {len(marketapp_requests)} ta so'rov:*\n\n"
            for r in marketapp_requests[:20]:
                msg += f"`{r[:100]}`\n"
        else:
            msg = "⚠️ marketapp.ws ga hech qanday so'rov ketmadi!"

        msg += f"\n\n📄 Sahifa: `{title}`\n📏 HTML hajmi: `{html_len}` belgi"

        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
        logger.info("Debug xabari yuborildi")


if __name__ == "__main__":
    asyncio.run(main())
