import requests
from bs4 import BeautifulSoup
import time
from telegram import Bot
import asyncio

# Sizning Telegram ma'lumotlarini kiriting
TELEGRAM_BOT_TOKEN = "7792255904:AAGr2X7iD0e9E5zpndOFxR3U0ng5V6ysQ-M"  # BotFatherdan olgan token
TELEGRAM_CHAT_ID = "747824671"      # Sizning chat ID

# Oldingi auksiyon IDlarini saqlash
seen_auctions = set()

async def send_telegram_message(message):
    """Telegram botga xabar yuborish"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"✅ Xabar yuborildi: {message}")
    except Exception as e:
        print(f"❌ Xabar yuborishda xato: {e}")

def check_fragment_auctions():
    """Fragment saytidagi yangi Gift auksiyon qidirish"""
    try:
        # Fragment API yoki saytni tekshirish
        url = "https://fragment.com/en/auction?filter=recently_listed"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Auksiyon kartalarini izlash
        auction_items = soup.find_all('div', class_='auction-card')
        
        for item in auction_items:
            try:
                # Auksiyon nomi va linki
                title_elem = item.find('a', class_='auction-title')
                if not title_elem:
                    continue
                
                auction_title = title_elem.get_text(strip=True)
                auction_link = title_elem.get('href', '')
                
                # Faqat Gift auksiyon uchun
                if 'gift' in auction_title.lower():
                    auction_id = auction_link.split('/')[-1] if auction_link else auction_title
                    
                    if auction_id not in seen_auctions:
                        seen_auctions.add(auction_id)
                        
                        # Narx va boshqa ma'lumot
                        price_elem = item.find('div', class_='auction-price')
                        price = price_elem.get_text(strip=True) if price_elem else "Narx noma'lum"
                        
                        # Xabar matn
                        message = f"""
🎁 YANGI GIFT AUKSIYON TOPILDI!

📝 Nomi: {auction_title}
💰 Narx: {price}
🔗 Havola: https://fragment.com{auction_link}
"""
                        
                        asyncio.run(send_telegram_message(message))
            
            except Exception as e:
                print(f"Auksiyon tahlilida xato: {e}")
                continue
    
    except Exception as e:
        print(f"❌ Fragment saytini tekshirishda xato: {e}")

def main():
    """Asosiy loop"""
    print("🤖 Fragment auksiyon boti ishga tushdi...")
    print(f"Bot har 10 sekundda tekshiriladi")
    
    while True:
        try:
            check_fragment_auctions()
            time.sleep(10)  # 10 sekundga kutish
        except KeyboardInterrupt:
            print("\n⛔ Bot to'xtatildi")
            break
        except Exception as e:
            print(f"Xato: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
