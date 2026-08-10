import time
import requests

# ==========================================
# تطبيق Nori Signals - صفقة 1 دقيقة (FastForex API)
# ==========================================
TELEGRAM_BOT_TOKEN = "8792506572:AAHH3hVOz895ca4W7-HaZ6bms1J_8kiFtXA"
TELEGRAM_CHAT_ID = "1792638515"

FASTFOREX_API_KEY = "3e4659f78c-2f97fec538-tjj1bw"

initial_balance = 1000.0
account_balance = initial_balance
BASE_PERCENT = 1.0        
current_percent = BASE_PERCENT

target_profit_pct = 10.0   
stop_loss_pct = 6.0        
session_profit = 0.0

SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
    "EUR/JPY", "EUR/GBP", "AUD/CHF", "AUD/JPY", "CAD/JPY"
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

def nori_strategy_loop():
    global current_percent, account_balance, session_profit
    
    send_telegram(
        "🚀 *تم تشغيل Nori Signals (الإشارة قبل افتتاح الشمعة بـ 30 ثانية)*\n"
        "📊 البوت يرسل الإشارة قبل بداية الشمعة الجديدة بـ 30 ثانية...\n"
        "🎯 الهدف: 10% | 🛑 الوقف: 6%"
    )
    
    last_prices = {}
    print("--- بدأ البوت في فحص الأسواق (الإشارة قبل 30 ثانية) ---")

    while True:
        try:
            target_dollar = initial_balance * (target_profit_pct / 100.0)
            stop_loss_dollar = initial_balance * (stop_loss_pct / 100.0)

            if session_profit >= target_dollar:
                send_telegram(f"🎯 *تم تحقيق هدف الربح (10%)!* (+${session_profit:.2f})")
                break
            if session_profit <= -stop_loss_dollar:
                send_telegram(f"🛑 *تم بلوغ حد الخسارة (6%)!* (-${abs(session_profit):.2f})")
                break

            current_time = time.localtime()
            current_min = current_time.tm_min
            current_sec = current_time.tm_sec

            # إرسال الإشارة قبل 30 ثانية من افتتاح الشمعة الجديدة (في آخر 30 ثانية من الشمعة الحالية)
            is_near_end_of_candle = ((current_min + 1) % 5 == 0) and (30 <= current_sec <= 59)

            if not is_near_end_of_candle:
                time.sleep(1)
                continue

            print("\n[*] ===== قبل افتتاح الشمعة بـ 30 ثانية: البحث عن فرصة للشمعة القادمة =====")
            
            selected_signal = None

            for symbol in SYMBOLS:
                print(f"[*] جاري فحص السعر للزوج: {symbol}...")
                price_start = get_fastforex_price(symbol)
                
                if not price_start:
                    continue

                print(f"[+] السعر الحالي لـ {symbol} هو: {price_start}")

                if symbol not in last_prices:
                    last_prices[symbol] = price_start
                    continue

                prev_price = last_prices[symbol]
                last_prices[symbol] = price_start  

                price_diff = price_start - prev_price
                last_digit = int(str(price_start).replace(".", "")[-1])
                
                if price_diff > 0 and last_digit >= 8:
                    action = 'PUT'
                elif price_diff < 0 and last_digit <= 2:
                    action = 'CALL'
                else:
                    print(f"[i] السوق مستقر لـ {symbol}")
                    continue

                selected_signal = {
                    "symbol": symbol,
                    "action": action,
                    "price_start": price_start
                }
                print(f"[🔥] تم العثور على فرصة للشمعة القادمة في {symbol}: {action}")
                break
                
                time.sleep(1)

            if not selected_signal:
                print("[i] لا توجد فرصة مطابقة للشروط في هذه اللحظة، بانتظار الفرصة القادمة...")
                time.sleep(5)
                continue

            symbol = selected_signal["symbol"]
            action = selected_signal["action"]
            price_start = selected_signal["price_start"]

            emoji = "🟢" if action == "CALL" else "🔴"
            
            signal_msg = (
                f"🚨 *إشارة مبكرة (الشمعة القادمة)*\n\n"
                f"📊 الزوج: `{symbol}`\n"
                f"{emoji} العملية للشمعة القادمة: *{action} (1 دقيقة)*\n"
                f"💵 مبلغ الصفقة: `{current_percent}%` من الرصيد\n"
                f"⏳ *الحالة:* تم الإرسال قبل افتتاح الشمعة بـ 30 ثانية، استعد للتنفيذ مع الافتتاح!"
            )
            send_telegram(signal_msg)

            print(f"[⏳] تم إرسال الإشارة المبكرة لـ {symbol}. جاري انتظار افتتاح الشمعة ومرور دقيقة...")
            
            start_wait = time.time()
            while time.time() - start_wait < 80:
                time.sleep(1)

            price_end = get_fastforex_price(symbol)
            if not price_end:
                price_end = price_start

            amount_to_trade = round((account_balance * current_percent) / 100.0, 2)
            if amount_to_trade < 1.0:
                amount_to_trade = 1.0

            # الاعتماد على لون الشمعة (اتجاه السعر بين البداية والنهاية للدقيقة)
            if action == 'CALL':
                is_win = price_end > price_start  # شمعة خضراء (صاعدة)
            else:  
                is_win = price_end < price_start  # شمعة حمراء (هابطة)

            if is_win:
                profit = round(amount_to_trade * 0.85, 2)
                account_balance += profit
                session_profit += profit
                current_percent = BASE_PERCENT  
                result_txt = f"ربح (+${profit:.2f}) ✅"
            else:
                account_balance -= amount_to_trade
                session_profit -= amount_to_trade
                current_percent *= 2  
                result_txt = f"خسارة (-${amount_to_trade}) ❌"

            print(f"[📊] نتيجة صفقة الدقيقة {symbol}: {result_txt}")
            result_msg = (
                f"📌 *نتيجة صفقة 1 دقيقة ({symbol}):*\n\n"
                f"العملية: *{action}*\n"
                f"السعر البدائي: `{price_start}` | السعر النهائي: `{price_end}`\n"
                f"النتيجة: *{result_txt}*\n"
                f"💰 إجمالي أرباح الجلسة: `${session_profit:.2f}`\n"
                f"💼 الرصيد الحالي: `${account_balance:.2f}`\n"
                f"────────────────"
            )
            send_telegram(result_msg)
            
            time.sleep(5)

        except Exception as err:
            print(f"Loop Error: {err}")
            time.sleep(5)

if __name__ == "__main__":
    nori_strategy_loop()
