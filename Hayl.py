import time
import requests

# ==========================================
# تطبيق Nori Signals - صفقة 5 دقائق (استراتيجية الأسباب الثلاثة)
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

def is_near_round_number(price):
    scaled = price * 1000
    remainder = scaled % 50
    return remainder < 5 or remainder > 45

def nori_strategy_loop():
    global current_percent, account_balance, session_profit, total_wins, total_losses
    
    send_telegram(
        "🚀 *تم تشغيل Nori Signals (فريم 5 دقائق)*\n"
        "📊 البوت يراقب السوق لإرسال الصفقات..."
    )
    
    candles_history = {symbol: [] for symbol in SYMBOLS}
    last_signal_time = {symbol: 0 for symbol in SYMBOLS}

    print("--- بدأ البوت العمل على فريم 5 دقائق ---")

    while True:
        try:
            selected_signal = None

            for symbol in SYMBOLS:
                current_price = get_fastforex_price(symbol)
                if not current_price:
                    continue

                # منع تكرار الإشارة لنفس الزوج إلا بعد مرور 10 دقائق (600 ثانية)
                if time.time() - last_signal_time[symbol] < 600:
                    continue

                history = candles_history[symbol]
                
                # بناء تاريخ الشمعات بالطريقة الأصلية السلسة
                if not history or time.localtime().tm_sec == 0:
                    if not history or history[-1].get("closed", True):
                        history.append({"open": current_price, "high": current_price, "low": current_price, "close": current_price, "closed": False})
                    else:
                        history[-1]["high"] = max(history[-1]["high"], current_price)
                        history[-1]["low"] = min(history[-1]["low"], current_price)
                        history[-1]["close"] = current_price
                else:
                    if history:
                        history[-1]["high"] = max(history[-1]["high"], current_price)
                        history[-1]["low"] = min(history[-1]["low"], current_price)
                        history[-1]["close"] = current_price
                        if time.localtime().tm_sec >= 58 and not history[-1].get("closed", False):
                            history[-1]["closed"] = True

                if len(history) >= 3:
                    c_prev = history[-2] 
                    c_curr = history[-1] 

                    is_uptrend = c_prev['close'] > c_prev['open']
                    is_downtrend = c_prev['close'] < c_prev['open']
                    near_rn = is_near_round_number(current_price)
                    is_green_candle = c_curr['close'] > c_curr['open']
                    is_red_candle = c_curr['close'] < c_curr['open']

                    action = None
                    if is_uptrend and near_rn and is_green_candle:
                        action = 'CALL'
                    elif is_downtrend and near_rn and is_red_candle:
                        action = 'PUT'

                    if action:
                        selected_signal = {"symbol": symbol, "action": action}
                        last_signal_time[symbol] = time.time()
                        break

                time.sleep(1)

            if not selected_signal:
                continue

            symbol = selected_signal["symbol"]
            action = selected_signal["action"]
            emoji = "🟢" if action == "CALL" else "🔴"
            
            signal_msg = (
                f"🚨 *إشارة جديدة (تأكيد الأسباب الثلاثة - 5 دقائق)*\n\n"
                f"📊 الزوج: `{symbol}`\n"
                f"{emoji} العملية للشمعة القادمة: *{action} (5 دقائق)*\n"
                f"✅ (ترند + روند نمبر + تأكيد شمعة)\n"
                f"💵 مبلغ الصفقة: `{current_percent}%` من الرصيد\n"
                f"⏳ *الحالة:* بانتظار نتيجة صفقة الـ 5 دقائق..."
            )
            send_telegram(signal_msg)

            # تسجيل سعر الدخول فوراً وقت إرسال الإشارة
            open_candle_price = get_fastforex_price(symbol) or 0.0

            # الانتظار لمدة 330 ثانية بالحرف من لحظة إرسال الإشارة
            time.sleep(330)

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
                f"📌 *نتيجة صفقة 5 دقائق ({symbol}):*\n\n"
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
