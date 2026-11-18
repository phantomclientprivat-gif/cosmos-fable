import datetime
import json
import os
import shutil
import time

DB_FILE = "cosmos_fable.json"
BACKUP_DIR = "backups"
WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def today_str():
    return datetime.date.today().isoformat()


def default_db():
    t = today_str()
    return {
        "updated_at": time.time(),
        "profile": {"weight": 70.0, "height": 175, "age": 18, "water": 0, "weight_history": []},
        "theme": {"name": "Квазар", "bg": "#1e222d", "card": "#262a36", "accent": "#7dd3fc"},
        "themes": [
            {"name": "Квазар", "bg": "#1e222d", "card": "#262a36", "accent": "#7dd3fc"},
            {"name": "Туманность", "bg": "#111827", "card": "#1e293b", "accent": "#38bdf8"},
            {"name": "Сверхновая", "bg": "#1c1427", "card": "#281d38", "accent": "#f472b6"},
            {"name": "Изумруд", "bg": "#0f1f1c", "card": "#162e29", "accent": "#34d399"},
        ],
        "food": {
            "date": t,
            "goal_kcal": 2200,
            "goal_p": 140,
            "goal_f": 70,
            "goal_c": 250,
            "logs": {t: []},
            "templates": [],
            "custom_products": [],
        },
        "workouts": {
            "step_idx": 0,
            "last_date": t,
            "done_today": False,
            "edit_idx": 0,
            "cycle": [
                {"name": "Тренировка 1", "rest": False, "ex": []},
                {"name": "День отдыха", "rest": True, "ex": []},
            ],
        },
        "ml": {
            "subtab": "roadmap",
            "filter": "Все",
            "stages": ["Личное", "Учеба", "Проекты"],
            "tasks": [],
            "notes": [],
        },
    }


def rollover(db):
    t = today_str()
    changed = False
    db.setdefault("food", {}).setdefault("logs", {}).setdefault(t, [])
    db["food"].setdefault("custom_products", [])
    db.setdefault("profile", {}).setdefault("weight_history", [])
    ml = db.setdefault("ml", {})
    for task in ml.get("tasks", []):
        if not task.get("done") and task.get("date", t) < t:
            task["date"] = t
            changed = True

    w = db.setdefault("workouts", {})
    cyc = w.get("cycle", [])
    if w.get("last_date", t) < t and cyc:
        idx = w.get("step_idx", 0) % len(cyc)
        if cyc[idx].get("rest") or w.get("done_today"):
            nxt = (idx + 1) % len(cyc)
            w["step_idx"], w["done_today"] = nxt, False
            for e in cyc[nxt]["ex"]:
                e["done"] = False
        w["last_date"] = t
        changed = True
    return db, changed


def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db, ch = rollover(json.load(f))
            if ch:
                save_db(db)
            return db
        except Exception:
            pass
    db = default_db()
    save_db(db)
    return db


def save_db(db):
    db["updated_at"] = time.time()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def create_backup():
    if not os.path.exists(DB_FILE):
        return "База еще не создана"
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    dst = os.path.join(BACKUP_DIR, f"backup_{stamp}.json")
    shutil.copy2(DB_FILE, dst)
    return f"Сохранено: {dst}"
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import httpx


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_wifi_server(state_ref, on_remote_update):
    class SyncHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path == "/sync":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(state_ref["db"], ensure_ascii=False).encode("utf-8"))

        def do_POST(self):
            if self.path == "/sync":
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                incoming = json.loads(raw)
                db, _ = rollover(incoming)
                state_ref["db"] = db
                save_db(db)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                on_remote_update(db)

    def run():
        try:
            srv = HTTPServer(("0.0.0.0", 8765), SyncHandler)
            srv.serve_forever()
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()


def sync_via_wifi(local_db, host_ip):
    ip = (host_ip or "").strip()
    if not ip:
        return local_db, "Укажи IP ПК"
    url = f"http://{ip}:8765/sync"
    try:
        with httpx.Client(timeout=3.0) as cl:
            r = cl.get(url)
            if r.status_code != 200:
                return local_db, f"Ошибка ({r.status_code})"
            remote_db = r.json()
            r_ts = float(remote_db.get("updated_at", 0))
            l_ts = float(local_db.get("updated_at", 0))
            if r_ts > l_ts + 1.0:
                db, _ = rollover(remote_db)
                save_db(db)
                return db, "Обновлено с ПК"
            elif l_ts > r_ts + 1.0:
                cl.post(url, content=json.dumps(local_db, ensure_ascii=False).encode("utf-8"))
                return local_db, "Отправлено на ПК"
            return local_db, "Синхронизировано"
    except Exception:
        return local_db, "ПК недоступен в Wi-Fi"
