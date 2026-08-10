import time
import requests
from datetime import datetime

# ==========================================
# تطبيق Nori Signals - النسخة النهائية المضبوطة بدقة
# ==========================================
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"

FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

initial_balance = 1000.0
account_balance = initial_balance
FIXED_PERCENT = 1.0        # نسبة ثابتة 1% بدون مضاعفات

target_profit_pct = 10.0   
stop_loss_pct = 6.0        
session_profit = 0.0

# الأسواق الأساسية فقط
SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY",
    "EUR/JPY", "EUR/GBP"
]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_fastforex_price(symbol):
    try:
        parts = symbol.split('/')
        if len(parts) != 2:
            return None
        base, quote = parts[0], parts[1]
        url = f"https://api.fastforex.io/fetch-one?from={base}&to={quote}&api_key={FASTFOREX_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if "result" in data and quote in data["result"]:
            return float(data["result"][quote])
    except Exception as e:
        print(f"API Error: {e}")
    return None

def is_allowed_trading_time():
    """فترات العمل: 9-11 صباحاً ومن 16-18 مساءً"""
    now = datetime.now()
    current_hour = now.hour
    
    morning_session = (9 <= current_hour < 11)
    evening_session = (16 <= current_hour < 18)
    
    return morning_session or evening_session

def nori_strategy_loop():
    global account_balance, session_profit
    
    send_telegram(
        "🚀 *تم تشغيل بوت Nori Signals (نسخة النتائج المضبوطة)*\n"
        "⏰ أوقات العمل: 09:00 - 11:00 ومن 16:00 - 18:00\n"
        "🎯 الهدف: 10% | 🛑 الوقف: 6% | 💵 نسبة ثابتة: 1%"
    )
    
    print("--- بدأ البوت بالعمل وفق الأوقات المحددة والنتائج الدقيقة ---")
    notified_outside_time = False

    while True:
        try:
            if not is_allowed_trading_time():
                if not notified_outside_time:
                    print("[i] خارج أوقات التداول المحددة. البوت في وضع الاستعداد...")
                    notified_outside_time = True
                time.sleep(30)
                continue
            
            if notified_outside_time:
                print("[i] تم دخول وقت التداول المحدد. البوت يعمل الآن...")
                notified_outside_time = False

            target_dollar = initial_balance * (target_profit_pct / 100.0)
            stop_loss_dollar = initial_balance * (stop_loss_pct / 100.0)

            if session_profit >= target_dollar:
                send_telegram(f"🎯 *تم تحقيق هدف الربح (10%)!* (+${session_profit:.2f})")
                time.sleep(300)
                continue
            if session_profit <= -stop_loss_dollar:
                send_telegram(f"🛑 *تم بلوغ حد الخسارة (6%)!* (-${abs(session_profit):.2f})")
                time.sleep(300)
                continue

            current_time = time.localtime()
            current_min = current_time.tm_min
            current_sec = current_time.tm_sec

            # مراقبة بداية شمعة 5 دقائق الجديدة (عند الدقيقة 00, 05, 10...)
            is_at_candle_start = (current_min % 5 == 0) and (0 <= current_sec <= 5)

            if not is_at_candle_start:
                time.sleep(1)
                continue

            print("\n[*] ===== بداية شمعة 5 دقائق: رصد الدقيقة الأولى =====")
            
            # تسجيل السعر عند بداية الدقيقة الأولى
            symbol_prices_start = {}
            for symbol in SYMBOLS:
                p = get_fastforex_price(symbol)
                if p:
                    symbol_prices_start[symbol] = p

            # انتظار مرور الدقيقة الأولى بالكامل (60 ثانية) لتحديد لونها
            print("[⏳] جاري انتظار انتهاء الدقيقة الأولى...")
            start_wait = time.time()
            while time.time() - start_wait < 62:
                time.sleep(1)

            selected_signal = None
            for symbol in SYMBOLS:
                if symbol not in symbol_prices_start:
                    continue
                
                price_start = symbol_prices_start[symbol]
                price_end_first_min = get_fastforex_price(symbol)
                
                if not price_end_first_min:
                    continue

                # تحديد اتجاه الصفقة حسب لون شمعة الدقيقة الأولى
                if price_end_first_min > price_start:
                    action = 'CALL'
                elif price_end_first_min < price_start:
                    action = 'PUT'
                else:
                    continue

                selected_signal = {
                    "symbol": symbol,
                    "action": action,
                    "entry_price": price_end_first_min
                }
                print(f"[🔥] تم تحديد الإشارة في {symbol}: {action} (سعر الدخول: {price_end_first_min})")
                break

            if not selected_signal:
                print("[i] لا توجد إشارة واضحة، بانتظار الشمعة القادمة...")
                time.sleep(10)
                continue

            symbol = selected_signal["symbol"]
            action = selected_signal["action"]
            entry_price = selected_signal["entry_price"]

            emoji = "🟢" if action == "CALL" else "🔴"
            
            signal_msg = (
                f"🚨 *إشارة تداول جديدة*\n\n"
                f"📊 الزوج: `{symbol}`\n"
                f"{emoji} العملية: *{action} (صفقة دقيقة واحدة)*\n"
                f"💵 سعر الدخول: `{entry_price}`\n"
                f"⏳ *الحالة:* جاري انتظار نتيجة الدقيقة..."
            )
            send_telegram(signal_msg)
            
            # الانتظار لمدة دقيقة واحدة بالضبط لحساب النتيجة بدقة
            start_trade_wait = time.time()
            while time.time() - start_trade_wait < 62:
                time.sleep(1)

            final_price = get_fastforex_price(symbol)
            if not final_price:
                final_price = entry_price

            amount_to_trade = round((account_balance * FIXED_PERCENT) / 100.0, 2)
            if amount_to_trade < 1.0:
                amount_to_trade = 1.0

            # حساب النتيجة بدقة تامة مقارنة سعر الدخول بسعر الإغلاق بعد دقيقة
            if action == 'CALL':
                is_win = final_price > entry_price
            else:  
                is_win = final_price < entry_price

            if is_win:
                profit = round(amount_to_trade * 0.85, 2)
                account_balance += profit
                session_profit += profit
                result_txt = f"ربح (+${profit:.2f}) ✅"
            else:
                account_balance -= amount_to_trade
                session_profit -= amount_to_trade
                result_txt = f"خسارة (-${amount_to_trade}) ❌"

            result_msg = (
                f"📌 *نتيجة صفقة ({symbol}):*\n\n"
                f"العملية: *{action}*\n"
                f"سعر الدخول: `{entry_price}` | سعر الإغلاق: `{final_price}`\n"
                f"النتيجة: *{result_txt}*\n"
                f"💰 إجمالي أرباح الجلسة: `${session_profit:.2f}`\n"
                f"💼 الرصيد الحالي: `${account_balance:.2f}`\n"
                f"────────────────"
            )
            send_telegram(result_msg)
            
            time.sleep(5)

        except Exception as err:
            print(f"Loop Error: {err}")
            time.sleep(10)

if __name__ == "__main__":
    nori_strategy_loop()
