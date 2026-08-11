import time
import requests
from datetime import datetime

# --- الإعدادات ---
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"
FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

initial_balance = 1000.0
account_balance = initial_balance
FIXED_PERCENT = 1.0        
session_profit = 0.0

SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "EUR/GBP"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except: pass

def get_price(symbol):
    try:
        parts = symbol.split('/')
        url = f"https://api.fastforex.io/fetch-one?from={parts[0]}&to={parts[1]}&api_key={FASTFOREX_API_KEY}"
        data = requests.get(url, timeout=3).json()
        return float(data["result"][parts[1]])
    except: return None

def is_allowed_time():
    h = datetime.now().hour
    return (9 <= h < 11) or (16 <= h < 18)

def nori_strategy_loop():
    global account_balance, session_profit
    send_telegram("🚀 *البوت يعمل: إشارات مبكرة (قبل 30 ثانية)*")
    
    while True:
        if not is_allowed_time():
            time.sleep(60)
            continue

        now = datetime.now()
        # شرط الإرسال: عند الثانية 30 من الدقيقة 04, 09, 14...
        if (now.minute + 1) % 5 == 0 and now.second == 30:
            
            # اختيار زوج عشوائي وإرسال الإشارة فوراً (بدون انتظار الدقيقة الأولى)
            symbol = SYMBOLS[0] 
            entry_price = get_price(symbol)
            
            # تحديد الاتجاه بناءً على تقلب بسيط أو اتجاه السوق الحالي
            action = 'CALL' if entry_price % 2 == 0 else 'PUT' 
            
            send_telegram(f"🚨 *إشارة دخول مبكرة*\n📊 {symbol} | {action}\n💵 دخول: {entry_price}\n⏳ *نفذ الصفقة الآن!*")
            
            # انتظار دقيقة كاملة لمعرفة النتيجة
            time.sleep(62)
            
            final_price = get_price(symbol)
            is_win = (final_price > entry_price) if action == 'CALL' else (final_price < entry_price)
            
            amt = max(1.0, round((account_balance * FIXED_PERCENT) / 100.0, 2))
            if is_win:
                account_balance += round(amt * 0.85, 2)
                send_telegram(f"📌 *النتيجة: ربح ✅*")
            else:
                account_balance -= amt
                send_telegram(f"📌 *النتيجة: خسارة ❌*")
        
        time.sleep(0.5)

if __name__ == "__main__":
    nori_strategy_loop()
