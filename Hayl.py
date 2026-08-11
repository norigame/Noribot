import time
import requests
from datetime import datetime

# --- الإعدادات الأساسية ---
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"
FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

account_balance = 1000.0
FIXED_PERCENT = 1.0        
target_profit_pct = 10.0   
stop_loss_pct = 6.0        
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
    send_telegram("🚀 *تم تشغيل بوت Nori Signals (فحص واختيار أقوى إشارة)*")
    
    while True:
        if not is_allowed_time():
            time.sleep(60)
            continue

        now = datetime.now()
        if (now.minute + 1) % 5 == 0 and now.second == 30:
            
            # فحص جميع الأزواج وحساب قوة التغير لكل واحد
            best_symbol = None
            max_change = -1.0
            best_action = 'CALL'
            
            for symbol in SYMBOLS:
                p1 = get_price(symbol)
                time.sleep(0.5)
                p2 = get_price(symbol)
                
                if p1 and p2:
                    change = abs(p2 - p1) / p1
                    if change > max_change:
                        max_change = change
                        best_symbol = symbol
                        best_action = 'CALL' if p2 >= p1 else 'PUT'
            
            if not best_symbol:
                best_symbol = SYMBOLS[0]
                best_action = 'CALL'

            symbol = best_symbol
            action = best_action
            emoji_action = '🟢' if action == 'CALL' else '🔴'
            
            amt = max(1.0, round((account_balance * FIXED_PERCENT) / 100.0, 2))
            
            msg = (
                f"🚨 *إشارة مبكرة (الشمعة القادمة - الأقوى)*\n\n"
                f"📊 الزوج: {symbol}\n"
                f"{emoji_action} العملية للشمعة القادمة: {action} (1 دقيقة)\n"
                f"💵 مبلغ الصفقة: {FIXED_PERCENT}% من الرصيد\n"
                f"⏳ الحالة: تم الإرسال قبل افتتاح الشمعة بـ 30 ثانية، استعد للتنفيذ مع الافتتاح!"
            )
            send_telegram(msg)
            
            time.sleep(32)
            open_price_candle = get_price(symbol)
            
            time.sleep(60)
            close_price_candle = get_price(symbol)
            
            is_win = (close_price_candle > open_price_candle) if action == 'CALL' else (close_price_candle < open_price_candle)
            
            profit_amt = round(amt * 0.85, 2)
            if is_win:
                account_balance += profit_amt
                session_profit += profit_amt
                result_msg = f"📌 *نتيجة صفقة 1 دقيقة ({symbol}):*\n\nالعملية: {action}\nالنتيجة: ربح (+${profit_amt})\n✅ إجمالي أرباح الجلسة: ${session_profit:.2f}\n💰 الرصيد الحالي: ${account_balance:.2f}"
            else:
                account_balance -= amt
                session_profit -= amt
                result_msg = f"📌 *نتيجة صفقة 1 دقيقة ({symbol}):*\n\nالعملية: {action}\nالنتيجة: خسارة (-${amt})\n❌ إجمالي أرباح الجلسة: ${session_profit:.2f}\n💰 الرصيد الحالي: ${account_balance:.2f}"
            
            send_telegram(result_msg)
            
        time.sleep(0.5)

if __name__ == "__main__":
    nori_strategy_loop()
