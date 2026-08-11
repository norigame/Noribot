import time
import requests
from datetime import datetime

# --- إعدادات البوت ---
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"
FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

initial_balance = 1000.0
account_balance = initial_balance
FIXED_PERCENT = 1.0        
target_profit_pct = 10.0   
stop_loss_pct = 6.0        
session_profit = 0.0

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
        base, quote = parts[0], parts[1]
        url = f"https://api.fastforex.io/fetch-one?from={base}&to={quote}&api_key={FASTFOREX_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if "result" in data and quote in data["result"]:
            return float(data["result"][quote])
    except: return None
    return None

def is_allowed_trading_time():
    now = datetime.now()
    return (9 <= now.hour < 11) or (16 <= now.hour < 18)

def nori_strategy_loop():
    global account_balance, session_profit
    send_telegram("🚀 *البوت يعمل (تنبيه قبل 30 ثانية من الشمعة)*")
    
    while True:
        if not is_allowed_trading_time():
            time.sleep(60)
            continue

        # الهدف: الإرسال عند الثانية 30 من الدقيقة 04, 09, 14... (أي قبل 30 ثانية من الشمعة الجديدة)
        now = datetime.now()
        current_min = now.minute
        current_sec = now.second
        
        # شرط الإرسال قبل 30 ثانية من بداية الشمعة (الدقائق التي تسبق 0, 5, 10...)
        if (current_min + 1) % 5 == 0 and current_sec == 30:
            print("[🔥] رصد الإشارة وإرسال التنبيه...")
            
            # 1. رصد السعر الحالي كـ 'سعر بداية'
            symbol_data = {}
            for s in SYMBOLS:
                p = get_fastforex_price(s)
                if p: symbol_data[s] = p

            # 2. إرسال تنبيه الاستعداد
            send_telegram("⏳ *إشارة مبكرة: استعد للتنفيذ خلال 30 ثانية!*")
            
            # انتظار بداية الشمعة الجديدة (الـ 30 ثانية المتبقية)
            time.sleep(35) 
            
            # 3. تحديد الاتجاه بناءً على حركة الدقيقة الأولى
            for s, entry_p in symbol_data.items():
                final_p = get_fastforex_price(s)
                if not final_p: continue
                
                action = 'CALL' if final_p > entry_p else 'PUT'
                
                # إرسال الإشارة
                send_telegram(f"🚨 *إشارة دخول*\n📊 {s} | {action}\n💵 دخول: {final_p}")
                
                # انتظار دقيقة الصفقة
                time.sleep(62)
                
                # حساب النتيجة
                end_p = get_fastforex_price(s)
                is_win = (end_p > final_p) if action == 'CALL' else (end_p < final_p)
                
                amt = max(1.0, round((account_balance * FIXED_PERCENT) / 100.0, 2))
                if is_win:
                    profit = round(amt * 0.85, 2)
                    account_balance += profit
                    session_profit += profit
                    send_telegram(f"📌 *نتيجة {s}: ربح ✅ (+${profit:.2f})*")
                else:
                    account_balance -= amt
                    session_profit -= amt
                    send_telegram(f"📌 *نتيجة {s}: خسارة ❌ (-${amt:.2f})*")
                break
        
        time.sleep(0.5)

if __name__ == "__main__":
    nori_strategy_loop()
