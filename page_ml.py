import os
import threading
import time
import flet as ft
from core import save_db, today_str
from i18n import tr, tr_item
from ui_kit import glass_card, pill_btn, styled_input


def build_ml_page(page: ft.Page, db: dict, theme: dict, file_picker: ft.FilePicker, open_sheet, close_sheet, play_click, toast, refresh):
    ml = db.setdefault("ml", {"subtab": "roadmap", "filter": "Все", "stages": ["Учеба", "Проекты", "Идеи"], "tasks": [], "notes": []})
    tasks = ml.setdefault("tasks", [])
    notes = ml.setdefault("notes", [])
    stages = ml.setdefault("stages", ["Учеба", "Проекты", "Идеи"])
    today = today_str()

    # Фокус-таймер для продуктивной работы (Pomodoro 25 мин)
    f_state = {"sec": 1500, "run": False}
    f_lbl = ft.Text("25:00", size=22, weight=ft.FontWeight.BOLD, color=theme["accent"])

    def focus_loop():
        while f_state["run"] and f_state["sec"] > 0:
            time.sleep(1)
            if not f_state["run"]:
                break
            f_state["sec"] -= 1
            f_lbl.value = f"{f_state['sec'] // 60:02d}:{f_state['sec'] % 60:02d}"
            try:
                page.update()
            except Exception:
                break
        if f_state["run"] and f_state["sec"] == 0:
            f_state["run"] = False
            toast("Фокус-сессия завершена! Сделай перерыв.")
            try:
                page.update()
            except Exception:
                pass

    def toggle_focus(e):
        play_click()
        if f_state["run"]:
            f_state["run"] = False
            e.control.content.controls[-1].value = tr(db, "start")
        else:
            if f_state["sec"] == 0:
                f_state["sec"] = 1500
            f_state["run"] = True
            e.control.content.controls[-1].value = tr(db, "pause")
            threading.Thread(target=focus_loop, daemon=True).start()
        page.update()

    def open_task_sheet(e):
        play_click()
        cur_f = ml.get("filter", "Все")
        act_st = cur_f if cur_f != "Все" else (stages if stages else "Общее")
        st_in = styled_input("Новая папка / раздел", theme)
        t_in = styled_input(f"Задача в «{act_st}»", theme)
        d_in = styled_input("Дата (ГГГГ-ММ-ДД)", theme, today)
        bulk_in = styled_input("Или вставь список задач (каждая с новой строки)", theme, multiline=True)

        def save_all(ev):
            play_click()
            target_st = st_in.value.strip() or act_st
            if st_in.value.strip() and st_in.value.strip() not in stages:
                stages.append(st_in.value.strip())
                ml["filter"] = st_in.value.strip()

            added = 0
            if t_in.value.strip():
                tasks.append({"id": int(time.time() * 1000), "stage": target_st, "title": t_in.value.strip(), "date": d_in.value.strip() or today, "done": False})
                added += 1

            for i_l, ln in enumerate(bulk_in.value.splitlines()):
                txt = ln.strip(" •-*0123456789.)\t")
                if txt:
                    tasks.append({"id": int(time.time() * 1000) + i_l + 1, "stage": target_st, "title": txt, "date": today, "done": False})
                    added += 1

            if added or st_in.value.strip():
                save_db(db)
                toast(f"Добавлено: {added}")
                close_sheet()
                refresh()

        open_sheet(ft.Column([
            ft.Text("Добавить в план", size=20, weight=ft.FontWeight.BOLD, color="#ffffff"),
            st_in, t_in, d_in, bulk_in,
            pill_btn("Сохранить", theme, save_all, icon=ft.Icons.CHECK),
        ], spacing=10, scroll=ft.ScrollMode.AUTO))

    def open_note_sheet(e):
        play_click()
        att = {"name": "", "content": ""}
        f_lbl_att = ft.Text("Файл не выбран", size=12, color="#94a3b8")

        def on_pick(ev):
            if ev.files:
                f = ev.files
                att["name"] = f.name
                if f.path and os.path.exists(f.path):
                    try:
                        with open(f.path, "r", encoding="utf-8", errors="ignore") as fp:
                            att["content"] = fp.read()[:12000]
                    except Exception:
                        pass
                f_lbl_att.value, f_lbl_att.color = f"Файл: {f.name}", theme["accent"]
                page.update()

        file_picker.on_result = on_pick
        tag_in = styled_input("Тег", theme, "Конспект")
        title_in = styled_input("Заголовок", theme)
        code_in = styled_input("Текст / Код", theme, multiline=True)

        def save_n(ev):
            play_click()
            if title_in.value.strip() or att["name"]:
                body = (code_in.value.strip() + "\n\n" + att["content"]).strip()
                notes.insert(0, {"tag": tag_in.value.strip() or "Заметка", "title": title_in.value.strip() or att["name"], "body": body, "file": att["name"]})
                save_db(db)
                toast("Заметка сохранена")
                close_sheet()
                refresh()

        open_sheet(ft.Column([
            ft.Text("Новая заметка", size=20, weight=ft.FontWeight.BOLD, color="#ffffff"),
            tag_in, title_in, code_in,
            ft.Row([pill_btn("Файл", theme, lambda ev: (play_click(), file_picker.pick_files()), icon=ft.Icons.ATTACH_FILE, filled=False, small=True), f_lbl_att]),
            pill_btn("Сохранить", theme, save_n, icon=ft.Icons.CHECK),
        ], spacing=10, scroll=ft.ScrollMode.AUTO))

    sub_bar = ft.Row([
        pill_btn(tr(db, "plans"), theme, lambda e: (play_click(), ml.update({"subtab": "roadmap"}), refresh()), filled=(ml.get("subtab") == "roadmap"), small=True),
        pill_btn(f"{tr(db, 'conspects')} ({len(notes)})", theme, lambda e: (play_click(), ml.update({"subtab": "notes"}), refresh()), filled=(ml.get("subtab") == "notes"), small=True),
        pill_btn(tr(db, "create").replace("+ ", ""), theme, open_task_sheet if ml.get("subtab") == "roadmap" else open_note_sheet, icon=ft.Icons.ADD, small=True),
    ], spacing=8)

    if ml.get("subtab") == "notes":
        n_cards = [
            glass_card(
                ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Text(n.get("tag", "Заметка"), size=10, color="#0f172a", weight=ft.FontWeight.BOLD), padding=ft.Padding.symmetric(horizontal=8, vertical=2), border_radius=6, bgcolor=theme["accent"]),
                        ft.Text(n["title"], size=14, weight=ft.FontWeight.BOLD, color="#ffffff", expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#64748b", icon_size=18, on_click=lambda e, i=i: (play_click(), notes.pop(i), save_db(db), refresh())),
                    ]),
                    ft.Text(f"Вложение: {n['file']}", size=11, color="#34d399") if n.get("file") else ft.Container(),
                    ft.Container(content=ft.Text(n["body"], size=12, color="#e2e8f0", selectable=True), padding=10, border_radius=10, bgcolor="#11141d", width=float("inf")) if n.get("body") else ft.Container(),
                ], spacing=6),
                theme, padding=12, radius=16,
            ) for i, n in enumerate(notes)
        ]
        return ft.Column([ft.Text(tr(db, "notes_title"), size=28, weight=ft.FontWeight.BOLD, color="#ffffff"), sub_bar, *(n_cards if n_cards else [ft.Text(tr(db, "empty"), color="#64748b")])], spacing=12)

    focus_card = glass_card(
        ft.Row([
            ft.Column([ft.Text(tr(db, "focus_timer"), size=12, color="#94a3b8"), f_lbl], spacing=0),
            ft.Row([
                pill_btn(tr(db, "start"), theme, toggle_focus, icon=ft.Icons.PLAY_ARROW, small=True),
                ft.IconButton(icon=ft.Icons.REFRESH, icon_color="#94a3b8", icon_size=20, on_click=lambda e: (play_click(), f_state.update({"run": False, "sec": 1500}), setattr(f_lbl, "value", "25:00"), page.update())),
            ], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        theme, accent_border=True, padding=14,
    )

    cur_f = ml.get("filter", "Все")
    chips = [
        ft.Container(
            content=ft.Text(tr_item(db, s), size=11, weight=ft.FontWeight.BOLD, color="#0f172a" if cur_f == s else "#cbd5e1"),
            padding=ft.Padding.symmetric(horizontal=10, vertical=6), border_radius=10,
            bgcolor=theme["accent"] if cur_f == s else ft.Colors.with_opacity(0.6, theme["card"]),
            ink=True, on_click=lambda e, st=s: (play_click(), ml.update({"filter": st}), refresh()),
        ) for s in (["Все"] + stages)
    ]

    t_cards = [
        glass_card(
            ft.Row([
                ft.Checkbox(value=t["done"], fill_color=theme["accent"], on_change=lambda e, idx=i: (play_click(), tasks[idx].update({"done": e.control.value}), save_db(db), refresh())),
                ft.Column([
                    ft.Text(f"{t.get('stage', 'План')} • {t.get('date', today)}", size=10, color=theme["accent"], weight=ft.FontWeight.BOLD),
                    ft.Text(t["title"], size=13, color="#64748b" if t["done"] else "#ffffff"),
                ], spacing=2, expand=True),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#64748b", icon_size=18, on_click=lambda e, idx=i: (play_click(), tasks.pop(idx), save_db(db), refresh())),
            ]),
            theme, padding=8, radius=16,
        ) for i, t in enumerate(tasks) if cur_f == "Все" or t.get("stage") == cur_f
    ]

    return ft.Column([ft.Text(tr(db, "notes_title"), size=28, weight=ft.FontWeight.BOLD, color="#ffffff"), sub_bar, focus_card, ft.Row(chips, wrap=True, spacing=6), *t_cards], spacing=12)
