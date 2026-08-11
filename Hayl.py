import time
import requests
from datetime import datetime, timedelta

# --- الإعدادات الأساسية ---
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"
FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

account_balance = 1000.0
FIXED_PERCENT = 1.0        
session_profit = 0.0

SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "EUR/GBP", 
    "AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF", "AUD/JPY", "CAD/JPY"
]

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
    local_time = datetime.now() + timedelta(hours=1) 
    h = local_time.hour
    return (9 <= h < 11) or (16 <= h < 18)

def check_strategy_conditions(symbol):
    # جلب قراءات متتالية لفحص الزخم والتقاطع بمرونة أكبر
    prices = []
    for _ in range(3):
        p = get_price(symbol)
        if p: prices.append(p)
        time.sleep(0.2)
    
    if len(prices) < 3:
        return None, None

    # شروط مرنة تعتمد على اتجاه الحركة الأخير والزخم
    momentum = abs(prices[2] - prices[0]) / prices[0]
    
    if momentum > 0.000001:  # عتبة خفيفة تضمن التقاط الحركة بدون تعقيد مفرط
        action = 'CALL' if prices[2] > prices[0] else 'PUT'
        return action, momentum
    
    return None, None

def nori_strategy_loop():
    global account_balance, session_profit
    send_telegram("🚀 *تم تشغيل بوت Nori Signals (بشروط مرنة ومنتظمة)*")
    
    while True:
        if not is_allowed_time():
            time.sleep(60)
            continue

        now = datetime.now()
        if (now.minute + 1) % 5 == 0 and now.second == 30:
            
            best_symbol = None
            best_action = 'CALL'
            max_mom = -1.0
            
            for symbol in SYMBOLS:
                action, mom = check_strategy_conditions(symbol)
                if action and mom and mom > max_mom:
                    max_mom = mom
                    best_symbol = symbol
                    best_action = action
            
            # إذا لم يتم العثور على زوج، نختار الزوج الأول افتراضياً لضمان عدم توقف الإشارات
            if not best_symbol:
                best_symbol = SYMBOLS[0]
                best_action = 'CALL'

            symbol = best_symbol
            action = best_action
            emoji_action = '🟢' if action == 'CALL' else '🔴'
            amt = max(1.0, round((account_balance * FIXED_PERCENT) / 100.0, 2))
            
            msg = (
                f"🚨 *إشارة جديدة*SYMBOLS\n\n"
                f"📊 الزوج: {symbol}\n"
                f"{emoji_action} العملية: {action} (1 دقيقة)\n"
                f"💵 مبلغ الصفقة: {FIXED_PERCENT}% من الرصيد\n"
                f"⏳ استعد للتنفيذ مع الافتتاح!"
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
                result_msg = f"📌 *نتيجة ({symbol}):* ربح ✅ (+${profit_amt})\n💰 الرصيد: ${account_balance:.2f}"
            else:
                account_balance -= amt
                session_profit -= amt
                result_msg = f"📌 *نتيجة ({symbol}):* خسارة ❌ (-${amt})\n💰 الرصيد: ${account_balance:.2f}"
            
            send_telegram(result_msg)
            
        time.sleep(0.5)

if __name__ == "__main__":
    nori_strategy_loop()
