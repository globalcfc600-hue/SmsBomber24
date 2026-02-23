import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ANA SAYFA VE SADE TASARIM
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>SMS Motoru</title>
        <style>
            body { background: #111; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { background: #222; padding: 40px; border-radius: 15px; border: 1px solid #444; text-align: center; }
            input { padding: 12px; width: 250px; border-radius: 8px; border: 1px solid #555; background: #000; color: #fff; margin-bottom: 20px; outline: none; }
            button { padding: 12px 30px; background: #00d2d3; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; color: #000; }
            #res { margin-top: 20px; color: #00d2d3; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>SMS Gönderici</h2>
            <input type="text" id="p" placeholder="5XXXXXXXXX" maxlength="10"><br>
            <button onclick="go()">BAŞLAT</button>
            <div id="res"></div>
        </div>
        <script>
            function go() {
                const p = document.getElementById('p').value;
                document.getElementById('res').innerText = "İşlem yapılıyor...";
                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({phone: p})
                }).then(r => r.json()).then(d => {
                    document.getElementById('res').innerText = "Sonuç: " + d.status;
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
    
    url = "https://api.kahvedunyasi.com/v1/login/otp"
    payload = {"mobile_number": phone, "channel": "sms"}
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        # BU SATIR PANELE DÖKER
        print(f">>> DURUM: {res.status_code} | HEDEF: {phone}", flush=True)
        return jsonify({"status": res.status_code})
    except Exception as e:
        print(f"HATA: {e}", flush=True)
        return jsonify({"status": "hata"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
