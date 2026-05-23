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
    await page.goto(URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(5)

    gifts = await page.evaluate("""() => {
        // ── 1: Next.js __NEXT_DATA__ dan qidirish ──────────────────────────
        function deepFindGifts(obj, depth) {
            if (!obj || depth > 6) return null;
            if (Array.isArray(obj) && obj.length > 0) {
                const f = obj[0];
                if (f && typeof f === 'object' && (
                    f.name || f.title || f.slug ||
                    f.gift_name || f.number || f.token_id
                )) return obj;
            }
            if (typeof obj === 'object') {
                for (const k of Object.keys(obj)) {
                    const r = deepFindGifts(obj[k], depth + 1);
                    if (r) return r;
                }
            }
            return null;
        }

        try {
            if (window.__NEXT_DATA__) {
                const found = deepFindGifts(window.__NEXT_DATA__, 0);
                if (found && found.length > 0) return found;
            }
        } catch(e) {}

        // ── 2: marketapp.ws API so'rovlaridan olish ─────────────────────────
        // (window.__marketData__ yoki shunga o'xshash global o'zgaruvchi)
        for (const key of Object.keys(window)) {
            try {
                const val = window[key];
                if (Array.isArray(val) && val.length > 0) {
                    const f = val[0];
                    if (f && typeof f === 'object' && (f.name || f.slug || f.number)) {
                        return val;
                    }
                }
            } catch(e) {}
        }

        // ── 3: DOM dan link orqali qidirish ─────────────────────────────────
        const results = [];
        const seen = new Set();

        document.querySelectorAll('a[href]').forEach(link => {
            const href = link.getAttribute('href') || '';
            const m = href.match(/\/gifts\/([a-zA-Z0-9_-]+)/);
            if (!m) return;

            const id = m[1];
            if (seen.has(id)) return;

            // Faqat raqamli yoki slug ko'rinishidagi IDlar (config fayllar emas)
            if (!/^[a-zA-Z0-9_-]{2,60}$/.test(id)) return;
            seen.add(id);

            const name = link.innerText.trim().substring(0, 120) || id;

            const priceEl = link.querySelector(
                '[class*="price"],[class*="bid"],[class*="ton"],[class*="amount"],[class*="floor"]'
            );
            const price = priceEl ? priceEl.innerText.trim() : '';

            results.push({ id, slug: id, name, price, href });
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

        logger.info("🚀 Monitoring boshlandi...")

        # ── BIRINCHI YUKLASH ───────────────────────────────────────────────────
        gifts = await scrape_gifts(page)
        logger.info(f"Birinchi run: {len(gifts)} ta gift")

        for gift in gifts:
            gid = str(gift.get("id") or gift.get("slug") or "").strip()
            if gid:
                seen_ids.add(gid)

        first_run = False

        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"✅ *Gift Monitor ishga tushdi!*\n\n"
                f"📦 *{len(seen_ids)} ta* gift kuzatilmoqda\n"
                f"⏱ Har *{CHECK_INTERVAL} soniya*da tekshiraman\n"
                f"🔔 Yangi gift paydo bo'lsa xabar beraman!"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── ASOSIY LOOP ────────────────────────────────────────────────────────
        while True:
            try:
                gifts = await scrape_gifts(page)
                logger.info(f"Tekshiruv: {len(gifts)} ta gift topildi")

                new_gifts = []
                for gift in gifts:
                    gid = str(gift.get("id") or gift.get("slug") or "").strip()
                    if gid and gid not in seen_ids:
                        seen_ids.add(gid)
                        new_gifts.append(gift)

                for gift in new_gifts:
                    name  = gift.get("name") or "Yangi Gift"
                    price = gift.get("price") or "—"
                    slug  = gift.get("slug") or gift.get("id") or ""
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
