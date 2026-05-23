import asyncio
import os
import logging
from playwright.async_api import async_playwright
from telegram import Bot
from telegram.constants import ParseMode

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
found_api_urls: list = []


def extract_gifts_from_data(data) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["items", "gifts", "data", "results", "nfts", "list", "docs"]:
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


async def main():
    global seen_ids, first_run, captured_gifts, found_api_urls

    bot = Bot(token=BOT_TOKEN)

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

        async def on_response(response):
            if response.status != 200:
                return
            try:
                data = await response.json()
                gifts = extract_gifts_from_data(data)
                if gifts:
                    resp_url = response.url
                    logger.info(f"✅ Gift API topildi: {resp_url} — {len(gifts)} ta gift")
                    captured_gifts.extend(gifts)
                    if resp_url not in found_api_urls:
                        found_api_urls.append(resp_url)
            except Exception:
                pass

        page.on("response", on_response)

        # ── BIRINCHI YUKLASH ───────────────────────────────────────────────────
        captured_gifts.clear()
        found_api_urls.clear()

        logger.info("Sahifa yuklanmoqda...")
        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(5)

        # Debug xabari yuborish
        if found_api_urls:
            debug = "🔍 *API topildi:*\n\n"
            for u in found_api_urls:
                debug += f"`{u}`\n\n"
            debug += f"Jami: *{len(captured_gifts)} ta gift*"
        else:
            debug = "⚠️ *Hech qanday Gift API topilmadi!*\n\nSayt boshqacha ishlaydi."

        await bot.send_message(chat_id=CHAT_ID, text=debug, parse_mode=ParseMode.MARKDOWN)

        # Barcha mavjud giftlarni "ko'rilgan" deb belgilash
        for gift in captured_gifts:
            gid = str(
                gift.get("id") or gift.get("_id") or
                gift.get("slug") or gift.get("token_id") or ""
            ).strip()
            if gid:
                seen_ids.add(gid)

        logger.info(f"{len(seen_ids)} ta gift birinchi run da saqlandi")
        first_run = False

        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"✅ *Gift Monitor tayyor!*\n\n"
                f"📦 Hozir *{len(seen_ids)} ta* gift kuzatilmoqda\n"
                f"⏱ Har *{CHECK_INTERVAL} soniya*da yangilanadi"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── ASOSIY LOOP ────────────────────────────────────────────────────────
        while True:
            try:
                captured_gifts.clear()

                await page.goto(URL, wait_until="networkidle", timeout=30_000)
                await asyncio.sleep(3)

                logger.info(f"Tekshiruv: {len(captured_gifts)} ta gift olindi")

                new_gifts = []
                for gift in captured_gifts:
                    gid = str(
                        gift.get("id") or gift.get("_id") or
                        gift.get("slug") or gift.get("token_id") or ""
                    ).strip()
                    if gid and gid not in seen_ids:
                        seen_ids.add(gid)
                        new_gifts.append(gift)

                for gift in new_gifts:
                    name  = gift.get("name") or gift.get("title") or "Yangi Gift"
                    price = (
                        gift.get("price") or gift.get("min_bid") or
                        gift.get("start_price") or "—"
                    )
                    slug  = gift.get("slug") or gift.get("id") or gift.get("_id") or ""
                    link  = f"https://marketapp.ws/gifts/{slug}" if slug else URL

                    text = (
                        "🎁 *Yangi Gift Auksionga Qo'yildi!*\n\n"
                        f"📦 *Nomi:* {name}\n"
                        f"💎 *Narx:* {price}\n"
                        f"\n[👉 Ko'rish]({link})"
                    )

                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    logger.info(f"✅ Xabar yuborildi: {name}")

                if not new_gifts:
                    logger.info(f"⏳ Yangi gift yo'q — {CHECK_INTERVAL}s")

            except Exception as e:
                logger.error(f"❌ Xato: {e}")
                try:
                    await page.reload(timeout=15_000)
                except Exception:
                    pass

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
