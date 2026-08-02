"""로그인 페이지."""
from __future__ import annotations

from nicegui import app, ui

from dashboard import theme
from dashboard.auth import DASHBOARD_PASSWORD


@ui.page("/login")
def login_page(redirect_to: str = "/"):
  if app.storage.user.get("authenticated", False):
    ui.navigate.to(redirect_to)
    return

  ui.add_head_html(theme.build_head_html())

  def try_login():
    if password_input.value == DASHBOARD_PASSWORD:
      app.storage.user["authenticated"] = True
      ui.navigate.to(redirect_to)
    else:
      ui.notify("비밀번호가 올바르지 않습니다", type="negative")

  with ui.column().classes("w-full items-center justify-center").style(
      "min-height: 100vh; background-color: var(--tbd-page-bg);"
  ):
    with ui.column().classes("tbd-card items-stretch gap-4").style("width: 320px;"):
      logo_uri = theme.logo_data_uri()
      if logo_uri:
        ui.html(f'<img src="{logo_uri}" style="height:32px;width:auto;margin-bottom:8px;" />', sanitize=False)
      ui.label("TBD Dashboard").classes("text-lg font-bold")
      password_input = ui.input("비밀번호", password=True, password_toggle_button=True).classes("w-full").props(
          "debounce=0"
      ).on("keydown.enter", try_login)
      ui.button("로그인", on_click=try_login).classes("w-full !bg-[#1A1B1E] !text-white")


@ui.page("/logout")
def logout_page():
  app.storage.user.clear()
  ui.navigate.to("/login")
