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
        await page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
    except Exception as e:
        logger.warning(f"Sahifani ochishda xato: {e}")
        return []

    await asyncio.sleep(5)

    gifts = await page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('a[href*="/gifts/"]').forEach(link => {
            const href  = link.getAttribute('href') || '';
            const match = href.match(/\\/gifts\\/([^/?#]+)/);
            if (!match) return;

            const id   = match[1];
            const name = (link.textContent || '').trim().substring(0, 120) || id;

            const priceEl = link.querySelector(
                '[class*="price"],[class*="bid"],[class*="ton"],[class*="amount"]'
            );
            const price = priceEl ? priceEl.textContent.trim() : '';

            const img    = link.querySelector('img');
            const imgSrc = img ? img.src : '';

            const timerEl = link.querySelector('[class*="timer"],[class*="time"],[class*="remaining"]');
            const timer   = timerEl ? timerEl.textContent.trim() : '';

            results.push({ id, name, price, href, imgSrc, timer });
        });
        return results;
    }""")

    return gifts


async def main():
    global seen_ids, first_run

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
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        logger.info("🚀 Monitoring boshlandi...")

        while True:
            try:
                gifts = await scrape_gifts(page)
                logger.info(f"Sahifada {len(gifts)} ta gift topildi")

                new_gifts = []
                for gift in gifts:
                    gid = gift.get("id", "").strip()
                    if gid and gid not in seen_ids:
                        seen_ids.add(gid)
                        if not first_run:
                            new_gifts.append(gift)

                first_run = False

                for gift in new_gifts:
                    name  = gift.get("name", "Noma'lum Gift")
                    price = gift.get("price") or "—"
                    timer = gift.get("timer") or ""
                    href  = gift.get("href", "")
                    link  = (
                        f"https://marketapp.ws{href}"
                        if href.startswith("/") else href
                    )

                    text = (
                        "🎁 *Yangi Gift Auksionga Qo'yildi!*\n\n"
                        f"📦 *Nomi:* {name}\n"
                        f"💎 *Narx:* {price}\n"
                        + (f"⏰ *Vaqt:* {timer}\n" if timer else "")
                        + f"\n[👉 Ko'rish]({link})"
                    )

                    try:
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=text,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=False,
                        )
                        logger.info(f"✅ Xabar yuborildi: {name}")
                    except Exception as e:
                        logger.error(f"Xabar yuborishda xato: {e}")

                if not new_gifts:
                    logger.info(f"⏳ Yangi gift yo'q — {CHECK_INTERVAL}s kutilmoqda...")

            except Exception as e:
                logger.error(f"❌ Asosiy xato: {e}")
                try:
                    await page.reload(timeout=15_000)
                except Exception:
                    pass

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
