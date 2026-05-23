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
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36")
        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(8)

        result = await page.evaluate("""() => {
            // Gift, card, item, nft nomli classlarni qidirish
            const keywords = ['gift', 'card', 'item', 'nft', 'lot', 'product', 'tile'];
            let found = [];

            for (const kw of keywords) {
                const els = document.querySelectorAll(`[class*="${kw}"]`);
                if (els.length > 3) {
                    found.push({
                        keyword: kw,
                        count: els.length,
                        sample: els[0].outerHTML.substring(0, 500)
                    });
                }
            }

            // Barcha a[href] lardan /gift yoki raqamli IDli linklar
            const allLinks = Array.from(document.querySelectorAll('a[href]'));
            const deepLinks = allLinks
                .map(a => a.getAttribute('href'))
                .filter(h => h && h.length > 8 && h !== '/gifts/' && h.includes('gift'))
                .slice(0, 5);

            return { classMatches: found, deepLinks };
        }""")

        msg = ""

        if result['classMatches']:
            msg += f"🎯 *Class topildi:*\n\n"
            for m in result['classMatches'][:4]:
                msg += f"`{m['keyword']}` → {m['count']} ta element\n"
                msg += f"```\n{m['sample'][:400]}\n```\n\n"

        if result['deepLinks']:
            msg += f"🔗 *Gift linklar:*\n"
            for l in result['deepLinks']:
                msg += f"`{l}`\n"

        if not msg:
            msg = "⚠️ Hech narsa topilmadi"

        if len(msg) > 4000:
            msg = msg[:4000] + "...(qisqartirildi)"

        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

if __name__ == "__main__":
    asyncio.run(main())
