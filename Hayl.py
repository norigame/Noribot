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
session_profit = 0.0
total_wins = 0
total_losses = 0

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

def check_round_number_break(prev_price, current_price):
    # تحديد الرقم الدائري (Round Number) بناءً على آخر رقمين 00
    # التحقق من تجاوز السعر لرقم منتهي بـ 00 والعودة لمسه أو اختراقه
    prev_int = int(prev_price * 10000)
    curr_int = int(current_price * 10000)
    
    # البحث عن أقرب رقم دائري منتهي بـ 100 (يعبر عن 00 في المراتب العشرية الكبرى)
    # فحص الاختراق والرجوع للمس
    for rn in range(round(prev_int / 100) * 100 - 200, round(prev_int / 100) * 100 + 300, 100):
        if (prev_int < rn <= curr_int) or (prev_int > rn >= curr_int):
            return True
    return False

def nori_strategy_loop():
    global current_percent, account_balance, session_profit, total_wins, total_losses
    
    send_telegram(
        "🚀 *تم تشغيل Nori Signals*\n"
        "📊 البوت يراقب الأسواق ليرسل أقوى إشارة قبل 30 ثانية..."
    )
    
    last_prices = {}
    last_signaled_symbol = None
    print("--- بدأ البوت في فحص الأسواق (الإشارة قبل 30 ثانية) ---")

    while True:
        try:
            current_time = time.localtime()
            current_min = current_time.tm_min
            current_sec = current_time.tm_sec

            is_near_end_of_candle = ((current_min + 1) % 5 == 0) and (30 <= current_sec <= 59)

            if not is_near_end_of_candle:
                time.sleep(1)
                continue

            selected_signal = None

            for symbol in SYMBOLS:
                if symbol == last_signaled_symbol:
                    continue

                price_start = get_fastforex_price(symbol)
                if not price_start:
                    continue

                if symbol not in last_prices:
                    last_prices[symbol] = price_start
                    continue

                prev_price = last_prices[symbol]
                last_prices[symbol] = price_start  

                price_diff = price_start - prev_price
                
                # التحقق من اختراق الرقم الدائري (Round Number 00)
                is_round_broken = check_round_number_break(prev_price, price_start)

                if is_round_broken:
                    if price_diff > 0:
                        action = 'CALL'
                    else:
                        action = 'PUT'
                else:
                    if price_diff > 0.0001:  
                        action = 'CALL'  
                    elif price_diff < -0.0001: 
                        action = 'PUT' 
                    else:
                        continue

                selected_signal = {
                    "symbol": symbol,
                    "action": action
                }
                print(f"[🔥] تم رصد أقوى إشارة في {symbol} للعملية: {action}")
                break
                
                time.sleep(1)

            if not selected_signal:
                time.sleep(5)
                continue

            symbol = selected_signal["symbol"]
            action = selected_signal["action"]
            
            last_signaled_symbol = symbol

            emoji = "🟢" if action == "CALL" else "🔴"
            
            signal_msg = (
                f"🚨 *إشارة مبكرة (أقوى إشارة)*\n\n"
                f"📊 الزوج: `{symbol}`\n"
                f"{emoji} العملية للشمعة القادمة: *{action} (1 دقيقة)*\n"
                f"💵 مبلغ الصفقة: `{current_percent}%` من الرصيد\n"
                f"⏳ *الحالة:* البوت يراقب الأسواق ليرسل أقوى إشارة قبل 30 ثانية!"
            )
            send_telegram(signal_msg)

            while True:
                t = time.localtime()
                if t.tm_sec == 0:
                    break
                time.sleep(0.1)

            open_candle_price = get_fastforex_price(symbol) or 0.0

            time.sleep(60)

            close_candle_price = get_fastforex_price(symbol) or open_candle_price

            amount_to_trade = round((account_balance * current_percent) / 100.0, 2)
            if amount_to_trade < 1.0:
                amount_to_trade = 1.0

            if action == 'CALL':
                is_win = close_candle_price > open_candle_price
            else:  
                is_win = close_candle_price < open_candle_price

            if is_win:
                profit = round(amount_to_trade * 0.85, 2)
                account_balance += profit
                session_profit += profit
                current_percent = BASE_PERCENT  
                total_wins += 1
                result_txt = f"ربح (+${profit:.2f}) ✅"
            else:
                account_balance -= amount_to_trade
                session_profit -= amount_to_trade
                current_percent *= 2  
                total_losses += 1
                result_txt = f"خسارة (-${amount_to_trade}) ❌"

            result_msg = (
                f"📌 *نتيجة صفقة 1 دقيقة ({symbol}):*\n\n"
                f"العملية: *{action}*\n"
                f"النتيجة: *{result_txt}*\n"
                f"📈 صفقات رابحة: `{total_wins}` | 📉 صفقات خاسرة: `{total_losses}`\n"
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
