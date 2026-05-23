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


async def scrape_gifts(page) -> list[dict]:
    try:
        await page.goto(URL, wait_until="networkidle", timeout=30_000)
    except Exception as e:
        logger.warning(f"Sahifa yuklanmadi: {e}")
        return []

    await asyncio.sleep(6)

    gifts = await page.evaluate("""() => {
        const results = [];
        const cards = document.querySelectorAll('.js-grid-card[data-nft-address]');

        cards.forEach(card => {
            const address = card.getAttribute('data-nft-address');
            if (!address) return;

            const linkEl = card.querySelector('a.tm-grid-item-link');
            const href   = linkEl ? linkEl.getAttribute('href') : '/nft/' + address + '/';

            const nameEl  = card.querySelector('[class*="name"],[class*="title"],[class*="label"]');
            const name    = nameEl ? nameEl.innerText.trim() : address.substring(0, 20);

            const priceEl = card.querySelector('[class*="price"],[class*="bid"],[class*="amount"],[class*="floor"]');
            const price   = priceEl ? priceEl.innerText.trim() : '';

            const timerEl = card.querySelector('[class*="timer"],[class*="time"],[class*="countdown"],[class*="remain"]');
            const timer   = timerEl ? timerEl.innerText.trim() : '';

            const imgEl   = card.querySelector('img');
            const img     = imgEl ? imgEl.src : '';

            results.push({ id: address, href, name, price, timer, img });
        });

        return results;
    }""")

    return gifts or []


async def main():
    global seen_ids, first_run

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

        # ── Birinchi yuklash — mavjud giftlarni saqlash ────────────────────────
        logger.info("Birinchi yuklash...")
        gifts = await scrape_gifts(page)
        logger.info(f"Birinchi run: {len(gifts)} ta gift")

        for gift in gifts:
            seen_ids.add(gift["id"])

        first_run = False

        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"✅ *Gift Monitor ishga tushdi!*\n\n"
                f"📦 *{len(seen_ids)} ta* gift kuzatilmoqda\n"
                f"⏱ Har *{CHECK_INTERVAL} soniya*da tekshiraman\n"
                f"🔔 Yangi auction gifti paydo bo'lsa xabar beraman!"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── Asosiy loop ────────────────────────────────────────────────────────
        while True:
            try:
                gifts = await scrape_gifts(page)
                logger.info(f"Tekshiruv: {len(gifts)} ta gift")

                new_gifts = []
                for gift in gifts:
                    if gift["id"] not in seen_ids:
                        seen_ids.add(gift["id"])
                        new_gifts.append(gift)

                for gift in new_gifts:
                    name  = gift.get("name")  or "Yangi Gift"
                    price = gift.get("price") or "—"
                    timer = gift.get("timer") or ""
                    href  = gift.get("href")  or ""
                    link  = f"https://marketapp.ws{href}" if href.startswith("/") else href

                    text = (
                        "🎁 *Yangi Gift Auksionga Qo'yildi!*\n\n"
                        f"📦 *Nomi:* {name}\n"
                        f"💎 *Narx:* {price}\n"
                        + (f"⏰ *Vaqt:* {timer}\n" if timer else "")
                        + f"\n[👉 Ko'rish]({link})"
                    )

                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    logger.info(f"✅ Yuborildi: {name}")

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
