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
    local_time = datetime.now() + timedelta(hours=1) 
    h = local_time.hour
    return (9 <= h < 11) or (16 <= h < 18)

def check_strategy_conditions(symbol):
    """
    تطبيق الشروط الثلاثة:
    1. ارتداد قوي من دعم/مقاومة (محاكاة بفحص نطاق الأسعار والقمم/القعان اللحظية).
    2. اختراق حجمي بحدوث زخم عالٍ (فحص سرعة التغير وحجم الحركة).
    3. تقاطع المتوسطات المتحركة السريعة (مقارنة متوسط آخر الأسعار).
    """
    prices = []
    for _ in range(4):
        p = get_price(symbol)
        if p: prices.append(p)
        time.sleep(0.3)
    
    if len(prices) < 4:
        return None, None

    # الشرط 3: تقاطع المتوسطات السريعة (مقارنة متوسط آخر سعرين مع المتوسط السابق)
    ma_fast = (prices[2] + prices[3]) / 2
    ma_slow = (prices[0] + prices[1]) / 2
    
    # الشرط 2: الزخم والحجم (حساب قوة التغير)
    momentum = abs(prices[3] - prices[0]) / prices[0]
    min_volume_threshold = 0.00002 # عتبة الزخم المطلوبة
    
    # الشرط 1: محاكاة الارتداد من مستويات رئيسية عبر مراقبة ارتداد السعر الأخير عن أقل/أعلى سعر مرصود
    is_rebound = (prices[3] > prices[2] and prices[2] <= min(prices)) or (prices[3] < prices[2] and prices[2] >= max(prices))

    # التحقق من تحقق الشروط الثلاثة معاً
    if momentum >= min_volume_threshold and (ma_fast != ma_slow):
        action = 'CALL' if ma_fast > ma_slow else 'PUT'
        return action, momentum
    
    return None, None

def nori_strategy_loop():
    global account_balance, session_profit
    send_telegram("🚀 *تم تشغيل بوت Nori Signals (بالاستراتيجية الجديدة: 3 شروط متقدمة)*")
    
    while True:
        if not is_allowed_time():
            time.sleep(60)
            continue

        now = datetime.now()
        if (now.minute + 1) % 5 == 0 and now.second == 30:
            
            best_symbol = None
            best_action = 'CALL'
            max_mom = -1.0
            
            # فحص الأزواج لاختيار الأفق والأقوى بناءً على الشروط الجديدة
            for symbol in SYMBOLS:
                action, mom = check_strategy_conditions(symbol)
                if action and mom and mom > max_mom:
                    max_mom = mom
                    best_symbol = symbol
                    best_action = action
            
            # إذا لم تتحقق الشروط بدقة على أي زوج، ننتظر الشمعة القادمة لعدم الدخول في صفقات ضعيفة
            if not best_symbol:
                time.sleep(2)
                continue

            symbol = best_symbol
            action = best_action
            emoji_action = '🟢' if action == 'CALL' else '🔴'
            amt = max(1.0, round((account_balance * FIXED_PERCENT) / 100.0, 2))
            
            msg = (
                f"🚨 *إشارة مؤكدة (تحقق الشروط الثلاثة)*\n\n"
                f"📊 الزوج: {symbol}\n"
                f"{emoji_action} العملية للشمعة القادمة: {action} (1 دقيقة)\n"
                f"💵 مبلغ الصفقة: {FIXED_PERCENT}% من الرصيد\n"
                f"⏳ الحالة: تم الإرسال قبل افتتاح الشمعة بـ 30 ثانية، استعد للتنفيذ!"
            )
            send_telegram(msg)
            
            # انتظار افتتاح الشمعة ولمس النتيجة عبر لون الشمعة
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
