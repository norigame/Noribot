import time
import requests

# ... (الإعدادات والـ Tokens تبقى كما هي) ...

def nori_strategy_loop():
    global current_percent, account_balance, session_profit, total_wins, total_losses
    send_telegram("🚀 *تم تشغيل Nori Signals - بنظام التهدئة*")
    
    while True:
        try:
            for symbol in SYMBOLS:
                price = get_fastforex_price(symbol)
                if not price: continue

                rn = check_round_number_touch(price)
                if rn is None: continue

                action = 'CALL' if price >= (rn/10000.0) else 'PUT'
                
                # إرسال الإشارة
                send_telegram(f"🚨 *إشارة فورية:* `{symbol}` | *{action}*")
                entry_price = price
                
                # حماية: انتظار انتهاء الشمعة (الدقيقة الحالية)
                # ننتظر حتى تصبح الثواني 00
                while time.localtime().tm_sec != 0:
                    time.sleep(0.5)
                time.sleep(1) 
                
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
                
                # هام جداً: إضافة فترة تهدئة (Cool-down) بعد كل صفقة
                # يمنع البوت من الإرسال الفوري مرة أخرى
                time.sleep(10) 
                
            time.sleep(2) # فحص الأرصدة
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    nori_strategy_loop()
