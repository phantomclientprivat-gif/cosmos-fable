from i18n import tr, tr_item
import datetime
from core import today_str
import threading
import flet as ft
from core import load_db, save_db, create_backup, get_local_ip, start_wifi_server, sync_via_wifi
from page_food import build_food_page
from page_gym import build_gym_page
from page_ml import build_ml_page
from ui_kit import glass_card, pill_btn, styled_input


def main(page: ft.Page):
    page.title = "Cosmos Fable"
    page.padding = 0
    page.window.width = 415
    page.window.height = 850
    page.theme = ft.Theme(page_transitions=ft.PageTransitionsTheme(android=ft.PageTransitionTheme.CUPERTINO, linux=ft.PageTransitionTheme.CUPERTINO))

    state = {"db": load_db(), "tab": 0}
    my_ip = get_local_ip()
    theme = state["db"]["theme"]
    page.bgcolor = theme["bg"]

    file_picker = ft.FilePicker()

    def make_audio(fn):
        try:
            a = ft.Audio(src=fn, autoplay=False)
            page.overlay.append(a)
            return a
        except Exception:
            return None

    click_snd, alarm_snd = make_audio("click.mp3"), make_audio("alarm.mp3")

    def play_click():
        if click_snd:
            try:
                click_snd.play()
            except Exception:
                pass

    def play_alarm():
        if alarm_snd:
            try:
                alarm_snd.play()
            except Exception:
                pass

    def toast(msg):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="#0f172a", weight=ft.FontWeight.BOLD), bgcolor=theme["accent"], duration=1600)
        page.snack_bar.open = True

    # Исправленная шторка без серого прямоугольника
    sheet_box = ft.Container(padding=20)
    bottom_sheet = ft.BottomSheet(
        content=sheet_box,
        bgcolor=theme.get("card", "#262a36"),
        shape=ft.RoundedRectangleBorder(radius=ft.BorderRadius.only(top_left=26, top_right=26)),
    )
    page.overlay.append(bottom_sheet)

    def open_sheet(content_control):
        sheet_box.content = content_control
        bottom_sheet.bgcolor = theme.get("card", "#262a36")
        bottom_sheet.open = True
        page.update()

    def close_sheet():
        bottom_sheet.open = False
        page.update()

    sync_lbl = ft.Text(tr(state["db"], "local_db"), size=11, color="#94a3b8")

    def run_sync(manual=False):
        if manual:
            play_click()
            res = create_backup()
            toast(res)
            page.update()

    def build_profile_page():
        prof = state["db"].setdefault("profile", {"weight": 70.0, "height": 175, "age": 16, "water": 0})
        food = state["db"]["food"]

        def open_macros_sheet(e):
            play_click()
            sel_goal = {"val": prof.get("goal_mode", "norm")}
            w_i = styled_input(tr(state["db"], "w_kg"), theme, prof.get("weight", 70), expand=True)
            h_i = styled_input(tr(state["db"], "h_cm"), theme, prof.get("height", 175), expand=True)
            a_i = styled_input(tr(state["db"], "age"), theme, prof.get("age", 16), expand=True)
            gk_i = styled_input(tr(state["db"], "kcal"), theme, food.get("goal_kcal", 2500), expand=True)
            gp_i = styled_input(tr(state["db"], "protein"), theme, food.get("goal_p", 150), expand=True)
            gf_i = styled_input(tr(state["db"], "fat"), theme, food.get("goal_f", 80), expand=True)
            gc_i = styled_input(tr(state["db"], "carbs"), theme, food.get("goal_c", 290), expand=True)

            goal_row = ft.Row(spacing=6)

            def render_goals():
                modes = [("cut", tr(state["db"], "cut")), ("norm", tr(state["db"], "norm")), ("bulk", tr(state["db"], "bulk"))]
                goal_row.controls = [
                    pill_btn(lbl, theme, lambda ev, m=m: (play_click(), sel_goal.update({"val": m}), render_goals(), auto_calc()), filled=(sel_goal["val"] == m), small=True)
                    for m, lbl in modes
                ]
                page.update()

            def auto_calc(ev=None):
                if ev:
                    play_click()
                try:
                    wt, ht, ag = float(w_i.value), float(h_i.value), int(a_i.value)
                    mult = {"cut": 0.85, "norm": 1.0, "bulk": 1.15}.get(sel_goal["val"], 1.0)
                    kcal = round((10 * wt + 6.25 * ht - 5 * ag + 5) * 1.45 * mult)
                    p = round(wt * (2.2 if sel_goal["val"] == "cut" else 2.0))
                    f = round(wt * (0.9 if sel_goal["val"] == "cut" else 1.0))
                    c = max(round((kcal - p * 4 - f * 9) / 4), 50)
                    gk_i.value, gp_i.value, gf_i.value, gc_i.value = str(kcal), str(p), str(f), str(c)
                    page.update()
                except ValueError:
                    toast("Проверь числа")
                    page.update()

            render_goals()

            def save_all(ev):
                play_click()
                try:
                    prof["weight"], prof["height"], prof["age"], prof["goal_mode"] = float(w_i.value), float(h_i.value), int(a_i.value), sel_goal["val"]
                    wh = prof.setdefault("weight_history", [])
                    wh.append({"date": today_str(), "w": prof["weight"]})
                    prof["weight_history"] = wh[-10:]
                    food["goal_kcal"], food["goal_p"], food["goal_f"], food["goal_c"] = int(gk_i.value), int(gp_i.value), int(gf_i.value), int(gc_i.value)
                    save_db(state["db"])
                    toast("Параметры сохранены")
                    close_sheet()
                    refresh()
                except ValueError:
                    toast("Введи числа")
                    page.update()

            open_sheet(ft.Column([
                ft.Text(tr(state["db"], "stats_sheet"), size=20, weight=ft.FontWeight.BOLD, color="#ffffff"),
                goal_row,
                ft.Row([w_i, h_i, a_i], spacing=8),
                ft.Row([gk_i, gp_i], spacing=8),
                ft.Row([gf_i, gc_i], spacing=8),
                ft.Row([pill_btn(tr(state["db"], "auto_calc"), theme, auto_calc, filled=False, small=True), pill_btn(tr(state["db"], "save"), theme, save_all, icon=ft.Icons.CHECK, small=True)], spacing=8),
            ], spacing=12, scroll=ft.ScrollMode.AUTO))

        def open_theme_sheet(e):
            play_click()
            n_i = styled_input(tr(state["db"], "theme_name"), theme)
            bg_i = styled_input(tr(state["db"], "bg_hex"), theme, theme["bg"])
            ac_i = styled_input(tr(state["db"], "acc_hex"), theme, theme["accent"])

            def add_th(ev):
                play_click()
                b = bg_i.value.strip() if bg_i.value.strip().startswith("#") else f"#{bg_i.value.strip()}"
                a = ac_i.value.strip() if ac_i.value.strip().startswith("#") else f"#{ac_i.value.strip()}"
                if len(b) == 7 and len(a) == 7:
                    item = {"name": n_i.value.strip() or "Космос", "bg": b, "card": b, "accent": a}
                    state["db"]["themes"].append(item)
                    apply_th(item)
                    close_sheet()

            open_sheet(ft.Column([ft.Text(tr(state["db"], "new_theme"), size=20, weight=ft.FontWeight.BOLD, color="#ffffff"), n_i, bg_i, ac_i, pill_btn(tr(state["db"], "create_theme"), theme, add_th, icon=ft.Icons.PALETTE)], spacing=10, scroll=ft.ScrollMode.AUTO))

        def apply_th(it):
            play_click()
            theme.update(it)
            state["db"]["theme"] = it.copy()
            save_db(state["db"])
            page.bgcolor = bg_layer.bgcolor = theme["bg"]
            nav_bar.active_color = theme["accent"]
            refresh()

        t_cards = [
            glass_card(
                ft.Row([
                    ft.Container(width=20, height=20, border_radius=10, bgcolor=it["accent"]),
                    ft.Text(tr_item(state["db"], it["name"]), size=15, weight=ft.FontWeight.BOLD, color="#ffffff", expand=True),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#64748b", icon_size=18, on_click=lambda e, x=it: (play_click(), state["db"]["themes"].remove(x), save_db(state["db"]), refresh())) if len(state["db"]["themes"]) > 1 else ft.Container(),
                ]),
                theme, padding=10, radius=16, accent_border=(it["name"] == theme["name"]), on_click=lambda e, x=it: apply_th(x),
            ) for it in state["db"]["themes"]
        ]


        logs = food.get("logs", {})
        goal_k = max(food.get("goal_kcal", 2500), 1)
        bars = []
        week_sum = 0
        for off in range(6, -1, -1):
            d_obj = datetime.date.today() - datetime.timedelta(days=off)
            d_str = d_obj.isoformat()
            day_k = sum(x.get("kcal", 0) for x in logs.get(d_str, []))
            week_sum += day_k
            h_px = max(6, min(int((day_k / goal_k) * 70), 85))
            bar_col = "#34d399" if 0.85 * goal_k <= day_k <= 1.15 * goal_k else (theme["accent"] if day_k > 0 else "#334155")
            bars.append(
                ft.Column([
                    ft.Text(f"{round(day_k)}", size=9, color="#94a3b8"),
                    ft.Container(width=22, height=h_px, border_radius=6, bgcolor=bar_col),
                    ft.Text(d_obj.strftime("%d.%m"), size=10, color="#cbd5e1"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3)
            )
        avg_k = round(week_sum / 7)
        wh_list = prof.get("weight_history", [])
        w_trend = f" • Динамика веса: {wh_list[-1]['w'] - wh_list['w']:+.1f} кг" if len(wh_list) >= 2 else ""
        analytics_card = glass_card(
            ft.Column([
                ft.Row([
                    ft.Text(tr(state["db"], "week_kcal"), size=15, weight=ft.FontWeight.BOLD, color=theme["accent"]),
                    ft.Text(tr(state["db"], "avg_kcal", k=avg_k), size=12, color="#94a3b8"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row(bars, alignment=ft.MainAxisAlignment.SPACE_AROUND, vertical_alignment=ft.CrossAxisAlignment.END),
                ft.Text(f"{tr(state['db'], 'bar_hint')}{w_trend}", size=11, color="#64748b"),
            ], spacing=10),
            theme,
        )

        return ft.Column([
            ft.Text(tr(state["db"], "profile_title"), size=28, weight=ft.FontWeight.BOLD, color="#ffffff"),
            glass_card(
                ft.Column([
                    ft.Row([ft.Text(tr(state["db"], "my_params"), size=16, weight=ft.FontWeight.BOLD, color=theme["accent"]), pill_btn(tr(state["db"], "edit"), theme, open_macros_sheet, icon=ft.Icons.EDIT, small=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(tr(state["db"], "stats_line", w=prof['weight'], h=prof['height'], a=prof['age']), size=13, color="#cbd5e1"),
                    ft.Text(tr(state["db"], "norm_line", k=food['goal_kcal'], p=food['goal_p'], f=food['goal_f'], c=food['goal_c']), size=13, color="#ffffff", weight=ft.FontWeight.W_600),
                ], spacing=6),
                theme, accent_border=True,
            ),
            analytics_card,

                        glass_card(
                ft.Row([
                    ft.Text(tr(state["db"], "lang_label"), size=14, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    ft.Row(
                        controls=[
                            pill_btn("RU", theme, lambda e: (play_click(), state["db"].update({"lang": "ru"}), save_db(state["db"]), update_nav_labels(), refresh()), filled=(state["db"].get("lang", "ru") == "ru"), small=True),
                            pill_btn("EN", theme, lambda e: (play_click(), state["db"].update({"lang": "en"}), save_db(state["db"]), update_nav_labels(), refresh()), filled=(state["db"].get("lang", "ru") == "en"), small=True),
                        ],
                        spacing=8,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                theme, padding=14,
            ),
            glass_card(
                ft.Row([
                    ft.Column([ft.Text(tr(state["db"], "water_bal"), size=14, weight=ft.FontWeight.BOLD, color="#38bdf8"), ft.Text(tr(state["db"], "drank", w=prof.get('water', 0)), size=13, color="#cbd5e1")], spacing=2),
                    ft.Row([
                        pill_btn(tr(state["db"], "add_water"), theme, lambda e: (play_click(), prof.update({"water": prof.get("water", 0) + 250}), save_db(state["db"]), refresh()), small=True),
                        ft.IconButton(icon=ft.Icons.REFRESH, icon_color="#64748b", icon_size=18, on_click=lambda e: (play_click(), prof.update({"water": 0}), save_db(state["db"]), refresh())),
                    ], spacing=4),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                theme, padding=14,
            ),
            ft.Row([ft.Text(tr(state["db"], "themes"), size=18, weight=ft.FontWeight.BOLD, color="#ffffff"), pill_btn(tr(state["db"], "custom_theme"), theme, open_theme_sheet, icon=ft.Icons.ADD, filled=False, small=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            *t_cards,
        ], spacing=12)

    switcher = ft.AnimatedSwitcher(
        content=ft.Container(),
        transition=ft.AnimatedSwitcherTransition.SCALE,
        duration=260,
        reverse_duration=180,
        switch_in_curve=ft.AnimationCurve.EASE_OUT_BACK,
        switch_out_curve=ft.AnimationCurve.EASE_IN,
        expand=True,
    )

    def refresh(animate=False):
        idx = state["tab"]
        if idx == 0:
            col = build_food_page(page, state["db"], theme, open_sheet, close_sheet, play_click, toast, refresh)
        elif idx == 1:
            col = build_gym_page(page, state["db"], theme, open_sheet, close_sheet, play_click, play_alarm, toast, refresh)
        elif idx == 2:
            col = build_ml_page(page, state["db"], theme, file_picker, open_sheet, close_sheet, play_click, toast, refresh)
        else:
            col = build_profile_page()
        col.scroll = ft.ScrollMode.AUTO
        switcher.content = ft.Container(content=col, key=f"tab_{idx}" if animate else switcher.content.key, expand=True)
        page.update()

    def switch_tab(new_idx):
        new_idx = max(0, min(3, new_idx))
        if new_idx != state["tab"]:
            play_click()
            state["tab"] = new_idx
            nav_bar.selected_index = new_idx
            refresh(animate=True)

    def on_swipe(e: ft.DragEndEvent):
        if e.primary_velocity and abs(e.primary_velocity) > 300:
            switch_tab(state["tab"] + (1 if e.primary_velocity < 0 else -1))

    gesture_area = ft.GestureDetector(
        content=ft.Container(content=ft.Container(content=switcher, width=760), alignment=ft.Alignment(0, -1), padding=ft.Padding.only(left=18, right=18, top=6, bottom=10), expand=True),
        on_horizontal_drag_end=on_swipe,
        expand=True,
    )

    top_bar = ft.Container(
        content=ft.Row([sync_lbl, ft.IconButton(icon=ft.Icons.SAVE_ALT, icon_color=theme["accent"], icon_size=20, on_click=lambda e: run_sync(True))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.only(left=18, right=10, top=10),
    )

    nav_bar = ft.CupertinoNavigationBar(
        bgcolor=ft.Colors.with_opacity(0.88, "#161922"),
        active_color=theme["accent"],
        inactive_color="#64748b",
        on_change=lambda e: switch_tab(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.RESTAURANT_OUTLINED, selected_icon=ft.Icons.RESTAURANT, label=tr(state["db"], "tab_food")),
            ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER_OUTLINED, selected_icon=ft.Icons.FITNESS_CENTER, label=tr(state["db"], "tab_gym")),
            ft.NavigationBarDestination(icon=ft.Icons.EDIT_NOTE_OUTLINED, selected_icon=ft.Icons.EDIT_NOTE, label=tr(state["db"], "tab_notes")),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label=tr(state["db"], "tab_profile")),
        ],
    )

    def update_nav_labels():
        sync_lbl.value = f"Wi-Fi IP: {my_ip}"
        nav_bar.destinations[0].label = tr(state["db"], "tab_food")
        nav_bar.destinations[1].label = tr(state["db"], "tab_gym")
        nav_bar.destinations[2].label = tr(state["db"], "tab_notes")
        nav_bar.destinations[3].label = tr(state["db"], "tab_profile")

    bg_layer = ft.Container(bgcolor=theme["bg"], expand=True)
    page.add(ft.Stack([bg_layer, ft.Image(src="space_bg.jpg", fit=ft.BoxFit.COVER, opacity=0.62, left=0, right=0, top=0, bottom=0, error_content=ft.Container()), ft.Column([top_bar, gesture_area, nav_bar], spacing=0, expand=True)], expand=True))

    refresh(animate=True)


ft.run(main, assets_dir="assets")
