import datetime
import threading
import time
import flet as ft
from core import WEEKDAYS, save_db
from i18n import tr, tr_item
from ui_kit import glass_card, pill_btn, styled_input


def build_gym_page(page: ft.Page, db: dict, theme: dict, open_sheet, close_sheet, play_click, play_alarm, toast, refresh):
    w = db["workouts"]
    cyc = w["cycle"]
    idx = w.get("step_idx", 0) % len(cyc)
    step = cyc[idx]
    today_wd = tr(db, "wd")[datetime.date.today().weekday()]

    t_state = {"sec": 0, "run": False}
    t_lbl = ft.Text("00:00", size=26, weight=ft.FontWeight.BOLD, color=theme["accent"])

    def loop():
        while t_state["run"] and t_state["sec"] > 0:
            time.sleep(1)
            if not t_state["run"]:
                break
            t_state["sec"] -= 1
            t_lbl.value = f"{t_state['sec'] // 60:02d}:{t_state['sec'] % 60:02d}"
            try:
                page.update()
            except Exception:
                break
        if t_state["run"] and t_state["sec"] == 0:
            t_state["run"] = False
            play_alarm()
            toast("Отдых завершен! К снаряду!")
            try:
                page.update()
            except Exception:
                pass

    def start_t(sec):
        play_click()
        t_state["sec"] = sec
        t_lbl.value = f"{sec // 60:02d}:{sec % 60:02d}"
        if not t_state["run"]:
            t_state["run"] = True
            threading.Thread(target=loop, daemon=True).start()
        page.update()

    def advance_cycle(e):
        play_click()
        nxt = (idx + 1) % len(cyc)
        w["step_idx"], w["done_today"] = nxt, False
        for x in cyc[nxt]["ex"]:
            x["done"] = False
        save_db(db)
        toast(f"Следующий этап: {cyc[nxt]['name']}")
        refresh()

    def open_cycle_editor(e):
        play_click()
        e_idx = w.get("edit_idx", 0) % len(cyc)
        ed = cyc[e_idx]
        name_in = styled_input(tr(db, "stage_name"), theme, tr_item(db, ed["name"]))
        rest_chk = ft.Checkbox(label=tr(db, "is_rest"), value=ed.get("rest", False), fill_color="#34d399")
        ex_n = styled_input(tr(db, "exercise"), theme, expand=True)
        ex_s = styled_input(tr(db, "sets"), theme, "4", width=62)
        ex_r = styled_input(tr(db, "reps"), theme, "10", width=66)

        tabs = [
            ft.Container(
                content=ft.Text(f"#{i + 1}", size=12, weight=ft.FontWeight.BOLD, color="#0f172a" if i == e_idx else "#ffffff"),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6), border_radius=8,
                bgcolor=("#34d399" if cyc[i].get("rest") else theme["accent"]) if i == e_idx else "#334155",
                ink=True, on_click=lambda ev, k=i: (play_click(), w.update({"edit_idx": k}), open_cycle_editor(None)),
            ) for i in range(len(cyc))
        ]

        ex_list = [
            ft.Row([
                ft.Text(f"• {x['name']} ({x['s']}×{x['r']})", color="#cbd5e1", size=13, expand=True),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#fb7185", icon_size=16, on_click=lambda ev, k=k: (play_click(), ed["ex"].pop(k), save_db(db), open_cycle_editor(None))),
            ]) for k, x in enumerate(ed["ex"])
        ]

        open_sheet(ft.Column([
            ft.Text(tr(db, "cycle_editor"), size=19, weight=ft.FontWeight.BOLD, color="#ffffff"),
            ft.Row([
                *tabs,
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=theme["accent"], on_click=lambda ev: (play_click(), cyc.append({"name": f"День {len(cyc)+1}", "rest": False, "ex": []}), w.update({"edit_idx": len(cyc)-1}), save_db(db), open_cycle_editor(None))),
                ft.IconButton(icon=ft.Icons.HOTEL, icon_color="#34d399", on_click=lambda ev: (play_click(), cyc.append({"name": "День отдыха", "rest": True, "ex": []}), w.update({"edit_idx": len(cyc)-1}), save_db(db), open_cycle_editor(None))),
            ], wrap=True),
            ft.Row([
                name_in,
                ft.IconButton(icon=ft.Icons.CHECK_CIRCLE, icon_color=theme["accent"], on_click=lambda ev: (play_click(), ed.update({"name": name_in.value.strip() or ed["name"], "rest": rest_chk.value}), save_db(db), refresh(), open_cycle_editor(None))),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#fb7185", on_click=lambda ev: (play_click(), cyc.pop(e_idx), w.update({"edit_idx": 0, "step_idx": 0}), save_db(db), refresh(), open_cycle_editor(None))) if len(cyc) > 1 else ft.Container(),
            ]),
            rest_chk,
            *([] if ed.get("rest") else [*ex_list, ft.Row([ex_n, ex_s, ex_r, ft.IconButton(icon=ft.Icons.ADD_BOX, icon_color=theme["accent"], on_click=lambda ev: (play_click(), ed["ex"].append({"name": ex_n.value.strip(), "s": ex_s.value or "4", "r": ex_r.value or "10", "done": False}), save_db(db), refresh(), open_cycle_editor(None)) if ex_n.value.strip() else None)], spacing=4)]),
        ], spacing=10, scroll=ft.ScrollMode.AUTO))

    if step.get("rest"):
        hero = glass_card(
            ft.Column([
                ft.Text(tr(db, "today_rest", wd=today_wd), size=13, color="#34d399", weight=ft.FontWeight.BOLD),
                ft.Text(tr_item(db, step["name"]), size=22, weight=ft.FontWeight.BOLD, color="#ffffff"),
                ft.Text(tr(db, "rest_desc"), size=13, color="#cbd5e1"),
                pill_btn(tr(db, "skip_rest"), theme, advance_cycle, small=True),
            ], spacing=10),
            theme, accent_border=True,
        )
    else:
        ex_rows = [
            ft.Row([
                ft.Checkbox(value=x["done"], fill_color=theme["accent"], on_change=lambda e, i=i: (play_click(), step["ex"][i].update({"done": e.control.value}), w.update({"done_today": all(z["done"] for z in step["ex"])}), save_db(db), refresh())),
                ft.Text(x["name"], size=14, weight=ft.FontWeight.W_600, color="#64748b" if x["done"] else "#ffffff", expand=True),
                ft.Container(content=ft.Text(f"{x['s']}×{x['r']}", size=12, color=theme["accent"], weight=ft.FontWeight.BOLD), padding=ft.Padding.symmetric(horizontal=8, vertical=4), border_radius=8, bgcolor=ft.Colors.with_opacity(0.15, theme["accent"])),
            ]) for i, x in enumerate(step["ex"])
        ]
        hero = glass_card(
            ft.Column([
                ft.Text(tr(db, "today_active", wd=today_wd), size=13, color=theme["accent"], weight=ft.FontWeight.BOLD),
                ft.Text(tr_item(db, step["name"]), size=22, weight=ft.FontWeight.BOLD, color="#ffffff"),
                *ex_rows,
                pill_btn(tr(db, "finish_workout"), theme, advance_cycle, icon=ft.Icons.CHECK, small=True),
            ], spacing=8),
            theme, accent_border=True,
        )

    timer_card = glass_card(
        ft.Row([
            ft.Column([ft.Text(tr(db, "rest_timer"), size=12, color="#94a3b8"), t_lbl], spacing=0),
            ft.Row([
                pill_btn(f"60{tr(db, 'sec')}", theme, lambda e: start_t(60), filled=False, small=True),
                pill_btn(f"90{tr(db, 'sec')}", theme, lambda e: start_t(90), filled=False, small=True),
                pill_btn(f"120{tr(db, 'sec')}", theme, lambda e: start_t(120), filled=False, small=True),
            ], spacing=6),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        theme, padding=14,
    )

    base_d = datetime.date.today()
    forecast = [
        ft.Row([
            ft.Text(f"{tr(db, "wd")[(base_d + datetime.timedelta(days=o)).weekday()]} • {(base_d + datetime.timedelta(days=o)).strftime('%d.%m')}", size=12, color="#94a3b8", width=85),
            ft.Text(tr_item(db, cyc[(idx + o) % len(cyc)]["name"]), size=13, color="#34d399" if cyc[(idx + o) % len(cyc)].get("rest") else "#ffffff", expand=True),
        ]) for o in range(1, 8)
    ]

    return ft.Column([
        ft.Row([ft.Text(tr(db, "gym_title"), size=28, weight=ft.FontWeight.BOLD, color="#ffffff"), pill_btn(tr(db, "cycle"), theme, open_cycle_editor, icon=ft.Icons.TUNE, filled=False, small=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        hero, timer_card,
        glass_card(ft.Column([ft.Text(tr(db, "forecast"), size=15, weight=ft.FontWeight.BOLD, color=theme["accent"]), *forecast], spacing=6), theme),
    ], spacing=12)
