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
