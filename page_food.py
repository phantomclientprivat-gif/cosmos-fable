import datetime
import flet as ft
from core import save_db, today_str
from i18n import tr
from products_db import PRODUCTS_DB
from ui_kit import glass_card, macro_ring, pill_btn, styled_input


def parse_num(val_str):
    s = str(val_str or "").strip().replace(",", ".")
    return float(s) if s else 0.0


def build_food_page(page: ft.Page, db: dict, theme: dict, open_sheet, close_sheet, play_click, toast, refresh):
    food = db["food"]
    sel_d = food.get("date") or today_str()
    eaten = food.setdefault("logs", {}).setdefault(sel_d, [])
    tpls = food.get("templates", [])
    custom_prods = food.setdefault("custom_products", [])

    kcal = round(sum(x.get("kcal", 0) for x in eaten), 1)
    prot = round(sum(x.get("p", 0) for x in eaten), 1)
    fat = round(sum(x.get("f", 0) for x in eaten), 1)
    carb = round(sum(x.get("c", 0) for x in eaten), 1)

    rem_p = max(round(food["goal_p"] - prot, 1), 0)
    rem_f = max(round(food["goal_f"] - fat, 1), 0)
    rem_c = max(round(food["goal_c"] - carb, 1), 0)

    def shift_d(delta):
        play_click()
        dt = datetime.date.fromisoformat(sel_d) + datetime.timedelta(days=delta)
        food["date"] = dt.isoformat()
        save_db(db)
        refresh()

    def add_food(name, k, p, f, c, as_tpl=False):
        play_click()
        item = {"name": name, "kcal": round(float(k), 1), "p": round(float(p), 1), "f": round(float(f), 1), "c": round(float(c), 1)}
        eaten.append(item)
        if as_tpl:
            tpls.append(item.copy())
        save_db(db)
        toast(f"+{item['kcal']} ккал • {name}")
        refresh()

    def open_add_sheet(e):
        play_click()
        search_in = styled_input(tr(db, "search_food"), theme)
        results_col = ft.Column(spacing=4)

        n_in = styled_input(tr(db, "dish_name"), theme)
        g_in = styled_input(tr(db, "weight_g"), theme, "100", width=95)
        k_in = styled_input(tr(db, "kcal_auto"), theme, width=105)
        p_in = styled_input(tr(db, "protein"), theme, width=78)
        f_in = styled_input(tr(db, "fat"), theme, width=78)
        c_in = styled_input(tr(db, "carbs"), theme, width=78)
        tpl_chk = ft.Checkbox(label=tr(db, "save_tpl"), value=False, fill_color=theme["accent"])
        db_chk = ft.Checkbox(label=tr(db, "save_db"), value=False, fill_color="#34d399")

        selected_prod = {"item": None}

        def recalc_kcal(ev=None):
            try:
                p_v, f_v, c_v = parse_num(p_in.value), parse_num(f_in.value), parse_num(c_in.value)
                k_in.value = str(round(p_v * 4.0 + f_v * 9.0 + c_v * 4.0, 1))
                page.update()
            except ValueError:
                pass

        p_in.on_change = recalc_kcal
        f_in.on_change = recalc_kcal
        c_in.on_change = recalc_kcal

        def apply_product(prod_dict):
            play_click()
            selected_prod["item"] = prod_dict
            try:
                grams = parse_num(g_in.value) or 100.0
                factor = grams / 100.0
                n_in.value = f"{prod_dict['name']} ({round(grams)}г)"
                p_in.value = str(round(prod_dict["p"] * factor, 1))
                f_in.value = str(round(prod_dict["f"] * factor, 1))
                c_in.value = str(round(prod_dict["c"] * factor, 1))
                results_col.controls.clear()
                recalc_kcal()
            except ValueError:
                pass

        g_in.on_change = lambda ev: apply_product(selected_prod["item"]) if selected_prod["item"] else None

        def filter_products(ev):
            q = search_in.value.strip().lower()
            results_col.controls.clear()
            if not q:
                page.update()
                return
            all_items = custom_prods + PRODUCTS_DB
            matches = [it for it in all_items if q in it["name"].lower()][:5]
            for it in matches:
                k_100 = round(it["p"] * 4 + it["f"] * 9 + it["c"] * 4)
                results_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(it["name"], size=13, color="#ffffff", weight=ft.FontWeight.W_500, expand=True),
                            ft.Text(f"{k_100} ккал • Б:{it['p']} Ж:{it['f']} У:{it['c']}", size=11, color=theme["accent"]),
                        ]),
                        padding=ft.Padding.symmetric(horizontal=10, vertical=8), border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.65, "#161922"),
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.3, theme["accent"])),
                        ink=True, on_click=lambda e, pr=it: apply_product(pr),
                    )
                )
            page.update()

        search_in.on_change = filter_products

        def submit(ev):
            if n_in.value.strip():
                try:
                    grams = parse_num(g_in.value) or 100.0
                    p_v, f_v, c_v = parse_num(p_in.value), parse_num(f_in.value), parse_num(c_in.value)
                    k_v = parse_num(k_in.value) if k_in.value.strip() else round(p_v * 4 + f_v * 9 + c_v * 4, 1)
                    if db_chk.value and grams > 0:
                        k_factor = 100.0 / grams
                        custom_prods.insert(0, {
                            "name": n_in.value.strip(),
                            "p": round(p_v * k_factor, 1),
                            "f": round(f_v * k_factor, 1),
                            "c": round(c_v * k_factor, 1),
                        })
                    add_food(n_in.value.strip(), k_v, p_v, f_v, c_v, tpl_chk.value)
                    close_sheet()
                except ValueError:
                    toast("Проверь числа")
                    page.update()

        open_sheet(ft.Column([
            ft.Text(tr(db, "add_meal"), size=20, weight=ft.FontWeight.BOLD, color="#ffffff"),
            search_in, results_col,
            ft.Divider(color="#334155", height=4),
            n_in,
            ft.Row([g_in, k_in], spacing=8),
            ft.Row([p_in, f_in, c_in], spacing=8),
            ft.Row([tpl_chk, db_chk], wrap=True),
            pill_btn(tr(db, "log_meal"), theme, submit, icon=ft.Icons.CHECK),
        ], spacing=8, scroll=ft.ScrollMode.AUTO))

    header = ft.Row([
        ft.Text(tr(db, "food_title"), size=28, weight=ft.FontWeight.BOLD, color="#ffffff"),
        ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=18, icon_color=theme["accent"], on_click=lambda e: shift_d(-1)),
                ft.Text(sel_d, size=13, weight=ft.FontWeight.BOLD, color="#ffffff"),
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=18, icon_color=theme["accent"], on_click=lambda e: shift_d(1)),
            ], spacing=0),
            border_radius=14, bgcolor=ft.Colors.with_opacity(0.6, theme["card"]),
        ),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    hero = glass_card(
        ft.Column([
            ft.Row([
                ft.Column([ft.Text(tr(db, "kcal_day"), size=13, color="#94a3b8"), ft.Text(f"{kcal} / {food['goal_kcal']}", size=24, weight=ft.FontWeight.BOLD, color=theme["accent"])], spacing=2),
                pill_btn(tr(db, "add"), theme, open_add_sheet, icon=ft.Icons.ADD, small=True),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.ProgressBar(value=min(kcal / max(food["goal_kcal"], 1), 1.0), color=theme["accent"], bgcolor=ft.Colors.with_opacity(0.15, "#ffffff"), height=8, border_radius=6),
            ft.Row([macro_ring(tr(db, "protein"), prot, food["goal_p"], "#38bdf8"), macro_ring(tr(db, "fat"), fat, food["goal_f"], "#fbbf24"), macro_ring(tr(db, "carbs"), carb, food["goal_c"], "#34d399")], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ft.Text(tr(db, "left_macro", p=rem_p, f=rem_f, c=rem_c), size=12, color="#94a3b8", text_align=ft.TextAlign.CENTER),
        ], spacing=12),
        theme, accent_border=True,
    )

    tpl_cards = [
        glass_card(
            ft.Row([
                ft.Column([ft.Text(t["name"], size=13, weight=ft.FontWeight.BOLD, color="#ffffff"), ft.Text(f"{t['kcal']} ккал • Б:{t['p']} Ж:{t['f']} У:{t['c']}", size=11, color="#94a3b8")], spacing=2, expand=True),
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=theme["accent"], icon_size=22, on_click=lambda e, x=t: add_food(x["name"], x["kcal"], x["p"], x["f"], x["c"])),
                ft.IconButton(icon=ft.Icons.CLOSE, icon_color="#64748b", icon_size=16, on_click=lambda e, i=i: (play_click(), tpls.pop(i), save_db(db), refresh())),
            ]),
            theme, padding=10, radius=16,
        ) for i, t in enumerate(tpls)
    ]

    eaten_cards = [
        glass_card(
            ft.Row([
                ft.Column([ft.Text(x["name"], size=14, weight=ft.FontWeight.W_600, color="#ffffff"), ft.Text(f"{x['kcal']} ккал • Б:{x['p']}г Ж:{x['f']}г У:{x['c']}г", size=12, color="#94a3b8")], spacing=2, expand=True),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="#fb7185", icon_size=18, on_click=lambda e, i=i: (play_click(), eaten.pop(i), save_db(db), refresh())),
            ]),
            theme, padding=10, radius=16,
        ) for i, x in enumerate(eaten)
    ]

    return ft.Column([
        header, hero,
        ft.Text(tr(db, "templates"), size=16, weight=ft.FontWeight.BOLD, color="#ffffff"),
        *(tpl_cards if tpl_cards else [ft.Text(tr(db, "no_templates"), size=12, color="#64748b")]),
        ft.Text(tr(db, "diary"), size=16, weight=ft.FontWeight.BOLD, color="#ffffff"),
        *(eaten_cards if eaten_cards else [ft.Text(tr(db, "empty"), size=12, color="#64748b")]),
    ], spacing=12)
