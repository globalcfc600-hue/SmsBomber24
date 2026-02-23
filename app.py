import os
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

def send_sms(phone):
    """Doğrudan SMS gönderen ve log basan fonksiyon"""
    url = "https://api.kahvedunyasi.com/v1/login/otp"
    payload = {"mobile_number": phone, "channel": "sms"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        # flush=True sayesinde Render panelinde anında görünür
        print(f">>> [{time.ctime()}] {phone} numarasina SMS gonderiliyor...", flush=True)
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f">>> [SONUC] Durum Kodu: {response.status_code} | Yanit: {response.text[:50]}", flush=True)
        return response.status_code
    except Exception as e:
        print(f">>> [HATA] Bir sorun olustu: {e}", flush=True)
        return None

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>SMS Motoru v3</title>
        <style>
            body { background: #121212; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .box { background: #1e1e1e; padding: 30px; border-radius: 10px; text-align: center; border: 1px solid #333; }
            input { padding: 10px; width: 200px; border-radius: 5px; border: none; margin-bottom: 10px; }
            button { padding: 10px 20px; background: #ff9f43; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>☕ Tekli SMS Başlat</h2>
            <input type="text" id="phone" placeholder="5XXXXXXXXX" maxlength="10"><br>
            <button onclick="run()">GÖNDER</button>
            <p id="msg"></p>
        </div>
        <script>
            function run() {
                const p = document.getElementById('phone').value;
                document.getElementById('msg').innerText = "Loglari kontrol et...";
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: p})
                }).then(res => res.json()).then(data => {
                    document.getElementById('msg').innerText = "Bitti: " + data.status;
                });
            }
        </script>
    </body>
    </html>
    """

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    phone = data.get('phone')
    
    if phone and len(phone) == 10:
        # Listeye ekleme yok, bekleme yok, direkt gönderim
        status = send_sms(phone)
        return jsonify({"status": status, "message": "Islem tamamlandi"})
    
    return jsonify({"status": "error", "message": "Gecersiz numara"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
