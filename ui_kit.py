import flet as ft


def glass_card(content, theme: dict, padding=16, radius=22, accent_border=False, on_click=None):
    border_col = ft.Colors.with_opacity(0.45 if accent_border else 0.16, theme["accent"])
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=radius,
        bgcolor=ft.Colors.with_opacity(0.76, theme.get("card", "#262a36")),
        border=ft.Border.all(1.2 if accent_border else 1.0, border_col),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=18,
            color=ft.Colors.with_opacity(0.22, "#000000"),
            offset=ft.Offset(0, 6),
        ),
        animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        ink=bool(on_click),
        on_click=on_click,
    )


def pill_btn(text: str, theme: dict, on_click, icon=None, filled=True, small=False):
    fg = "#0f172a" if filled else "#ffffff"
    bg = theme["accent"] if filled else ft.Colors.with_opacity(0.14, theme["accent"])
    row_items = [ft.Icon(icon, size=16 if small else 18, color=fg)] if icon else []
    row_items.append(ft.Text(text, size=12 if small else 14, weight=ft.FontWeight.BOLD, color=fg))
    return ft.Container(
        content=ft.Row(row_items, spacing=6, alignment=ft.MainAxisAlignment.CENTER, tight=True),
        padding=ft.Padding.symmetric(horizontal=14 if small else 18, vertical=8 if small else 12),
        border_radius=14 if small else 16,
        bgcolor=bg,
        border=None if filled else ft.Border.all(1, ft.Colors.with_opacity(0.4, theme["accent"])),
        ink=True,
        on_click=on_click,
    )


def macro_ring(label: str, val: float, goal: float, color: str):
    ratio = min(val / max(goal, 1), 1.0)
    return ft.Column(
        [
            ft.Stack(
                [
                    ft.ProgressRing(value=ratio, width=56, height=56, stroke_width=5, color=color, bgcolor=ft.Colors.with_opacity(0.15, "#ffffff")),
                    ft.Container(
                        content=ft.Text(f"{round(val)}", size=12, weight=ft.FontWeight.BOLD, color="#ffffff"),
                        width=56, height=56, alignment=ft.Alignment(0, 0),
                    ),
                ]
            ),
            ft.Text(label, size=11, color="#cbd5e1"),
            ft.Text(f"/{round(goal)}", size=10, color="#64748b"),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2,
    )


def styled_input(label: str, theme: dict, value="", width=None, expand=False, multiline=False):
    return ft.TextField(
        label=label,
        value=str(value),
        width=width,
        expand=expand,
        multiline=multiline,
        min_lines=2 if multiline else 1,
        max_lines=4 if multiline else 1,
        border_color=ft.Colors.with_opacity(0.4, theme["accent"]),
        focused_border_color=theme["accent"],
        color="#ffffff",
        label_style=ft.TextStyle(color="#94a3b8", size=12),
        border_radius=14,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
    )
