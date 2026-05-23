import asyncio
import os
import logging
from playwright.async_api import async_playwright
from telegram import Bot
from telegram.constants import ParseMode
import json

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN      = os.environ["BOT_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "15"))

URL = (
    "https://marketapp.ws/gifts/"
    "?tab=nfts&sort_by=recently_touch&filter_by=auction_no_bids"
)

seen_ids: set = set()
first_run: bool = True
captured_gifts: list = []


def extract_gifts_from_data(data) -> list:
    """JSON dan gift ro'yxatini olish"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["items", "gifts", "data", "results", "nfts", "list"]:
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


async def main():
    global seen_ids, first_run, captured_gifts

    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "✅ *Gift Monitor ishga tushdi!*\n\n"
                f"⏱ Har *{CHECK_INTERVAL} soniya*da tekshiraman\n"
                "🔔 Yangi auction gifti paydo bo'lsa darhol xabar beraman!"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        logger.error(f"Start xabarida xato: {e}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        # ── API javoblarini tutib olish ────────────────────────────────────────
        async def on_response(response):
            url = response.url
            if response.status != 200:
                return
            # JSON qaytaradigan so'rovlar
            ct = response.headers.get("content-type", "")
            if "json" not in ct:
                return
            try:
                data = await response.json()
                gifts = extract_gifts_from_data(data)
                if gifts:
                    logger.info(f"API topildi: {url} — {len(gifts)} ta gift")
                    captured_gifts.extend(gifts)
            except Exception:
                pass

        page.on("response", on_response)

        logger.info("🚀 Monitoring boshlandi...")

        while True:
            try:
                captured_gifts.clear()

                await page.goto(URL, wait_until="networkidle", timeout=30_000)
                await asyncio.sleep(3)

                logger.info(f"Jami {len(captured_gifts)} ta gift API dan olindi")

                new_gifts = []
                for gift in captured_gifts:
                    # ID ni turli nomlar bilan qidirish
                    gid = str(
                        gift.get("id") or
                        gift.get("_id") or
                        gift.get("slug") or
                        gift.get("token_id") or
                        gift.get("number") or
                        ""
                    ).strip()

                    if gid and gid not in seen_ids:
                        seen_ids.add(gid)
                        if not first_run:
                            new_gifts.append(gift)

                first_run = False

                for gift in new_gifts:
                    # Nom
                    name = (
                        gift.get("name") or
                        gift.get("title") or
                        gift.get("gift_name") or
                        "Yangi Gift"
                    )
                    # Narx
                    price = (
                        gift.get("price") or
                        gift.get("min_bid") or
                        gift.get("start_price") or
                        gift.get("floor_price") or
                        "—"
                    )
                    # Link
                    slug = (
                        gift.get("slug") or
                        gift.get("id") or
                        gift.get("_id") or
                        ""
                    )
                    link = f"https://marketapp.ws/gifts/{slug}" if slug else URL

                    text = (
                        "🎁 *Yangi Gift Auksionga Qo'yildi!*\n\n"
                        f"📦 *Nomi:* {name}\n"
                        f"💎 *Narx:* {price}\n"
                        f"\n[👉 Ko'rish]({link})"
                    )

                    try:
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=text,
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        logger.info(f"✅ Xabar yuborildi: {name}")
                    except Exception as e:
                        logger.error(f"Xabar yuborishda xato: {e}")

                if not new_gifts:
                    logger.info(f"⏳ Yangi gift yo'q — {CHECK_INTERVAL}s kutilmoqda...")

            except Exception as e:
                logger.error(f"❌ Xato: {e}")
                try:
                    await page.reload(timeout=15_000)
                except Exception:
                    pass

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
