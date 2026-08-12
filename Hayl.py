import time
import requests

# ==========================================
# تطبيق Nori Signals - صفقة 1 دقيقة
# ==========================================
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"
FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

initial_balance = 1000.0
account_balance = initial_balance
BASE_PERCENT = 1.0        
current_percent = BASE_PERCENT
session_profit = 0.0
total_wins = 0
total_losses = 0

SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "EUR/GBP"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_fastforex_price(symbol):
    try:
        parts = symbol.split('/')
        url = f"https://api.fastforex.io/fetch-one?from={parts[0]}&to={parts[1]}&api_key={FASTFOREX_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data["result"][parts[1]])
    except: return None

def check_round_number_touch(price):
    p_int = int(price * 10000)
    return round(p_int / 100) * 100 if (p_int % 100 <= 5 or p_int % 100 >= 95) else None

def nori_strategy_loop():
    global current_percent, account_balance, session_profit, total_wins, total_losses
    send_telegram("🚀 *تم تشغيل Nori Signals*")
    last_signaled_symbol = None
    
    while True:
        try:
            for symbol in SYMBOLS:
                price = get_fastforex_price(symbol)
                if not price or symbol == last_signaled_symbol: continue

                rn = check_round_number_touch(price)
                if rn is None: continue

                action = 'CALL' if price >= (rn/10000.0) else 'PUT'
                last_signaled_symbol = symbol
                
                # إرسال الإشارة فوراً
                send_telegram(f"🚨 *إشارة فورية:* `{symbol}` | *{action}*")
                entry_price = price
                
                # الانتظار حتى نهاية الدقيقة الحالية (حتى تغلق الشمعة)
                # ننتظر حتى تصبح الثواني 00 والدقيقة التالية
                while time.localtime().tm_sec != 0:
                    time.sleep(0.5)
                time.sleep(1) # ضمان إغلاق الشمعة
                
                close_price = get_fastforex_price(symbol) or entry_price
                
                # تقييم النتيجة
                amount = round((account_balance * current_percent) / 100.0, 2)
                is_win = (action == 'CALL' and close_price > entry_price) or (action == 'PUT' and close_price < entry_price)
                
                if is_win:
                    profit = round(amount * 0.85, 2)
                    account_balance += profit
                    session_profit += profit
                    current_percent = BASE_PERCENT
                    total_wins += 1
                    res = "ربح ✅"
                else:
                    account_balance -= amount
                    session_profit -= amount
                    current_percent *= 2
                    total_losses += 1
                    res = "خسارة ❌"
                
                send_telegram(f"📌 *النتيجة ({symbol}):* {res}\n💰 الرصيد: `${account_balance:.2f}`")
                
            time.sleep(2)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    nori_strategy_loop()
