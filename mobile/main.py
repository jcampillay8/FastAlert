import flet as ft
import httpx
import asyncio

# --- CONFIGURACIÓN ---
API_URL = "http://192.168.100.32:8000/api/v1/alarma"

async def main(page: ft.Page):
    page.title = "FastAlert"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    state = {"phone": None}

    # Recuperar teléfono
    try:
        if hasattr(page, "client_storage") and page.client_storage is not None:
            val = page.client_storage.get("user_phone")
            if val: state["phone"] = val
    except: pass

    # --- DIÁLOGOS ---
    async def close_success_dlg(e):
        success_dialog.open = False
        page.update()

    success_dialog = ft.AlertDialog(
        title=ft.Text("✅ SISTEMA ACTIVADO"),
        content=ft.Text("ALERTA ENVIADA CON ÉXITO\n\nEl vecindario y el sistema de cámaras han sido notificados.", text_align="center"),
        actions=[
            ft.TextButton("ENTENDIDO", on_click=close_success_dlg),
        ],
    )
    page.overlay.append(success_dialog)

    async def handle_confirm(e):
        confirm_dialog.open = False
        page.update()
        await send_panic_alert()

    async def close_dlg(e):
        confirm_dialog.open = False
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ CONFIRMAR"),
        content=ft.Text("¿Activar la alerta ahora?"),
        actions=[
            ft.TextButton("SÍ, ACTIVAR", on_click=handle_confirm, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("NO", on_click=close_dlg),
        ],
    )
    page.overlay.append(confirm_dialog)

    async def open_confirmation(e):
        confirm_dialog.open = True
        page.update()

    # --- LÓGICA DE ALERTA ---
    async def send_panic_alert():
        phone = state["phone"]
        
        page.snack_bar = ft.SnackBar(ft.Text("🚀 Procesando alerta..."), bgcolor=ft.Colors.BLUE_GREY_800)
        page.snack_bar.open = True
        
        panic_button.disabled = True
        panic_button.opacity = 0.5
        page.update()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(f"{API_URL}/activar", json={"telefono": phone})
                data = response.json()
                
                if response.status_code == 200:
                    if data.get("status") == "already_active":
                        msg, color = "ℹ️ La alarma ya está activa. Espera un momento.", ft.Colors.BLUE_700
                        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
                        page.snack_bar.open = True
                    else:
                        # Éxito explícito con Diálogo
                        success_dialog.open = True
                        page.update()
                else:
                    msg, color = f"❌ Error API: {response.status_code}", ft.Colors.RED_700
                    page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
                    page.snack_bar.open = True
        except Exception as e:
            msg, color = f"🚨 Error de Red: {str(e)}", ft.Colors.RED_900
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            page.snack_bar.open = True
        
        panic_button.disabled = False
        panic_button.opacity = 1.0
        page.update()

    async def send_reset_alert(e):
        page.snack_bar = ft.SnackBar(ft.Text("🔄 Rearmando sistema..."), bgcolor=ft.Colors.BLUE_GREY_800)
        page.snack_bar.open = True
        page.update()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{API_URL}/desactivar")
                if response.status_code == 200:
                    msg, color = "🔄 SISTEMA REARMADO CORRECTAMENTE", ft.Colors.BLUE_800
                else:
                    msg, color = f"❌ Error API: {response.status_code}", ft.Colors.RED_700
        except Exception as e:
            msg, color = f"🚨 Error de Red: {str(e)}", ft.Colors.RED_900

        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    # --- COMPONENTES ---
    panic_button = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.GPP_BAD, size=80, color=ft.Colors.WHITE),
                ft.Text("ACTIVAR\nALERTA", size=30, weight="bold", text_align="center"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=280,
        height=280,
        bgcolor=ft.Colors.RED_700,
        shape=ft.BoxShape.CIRCLE,
        on_click=open_confirmation,
    )

    phone_input = ft.TextField(
        label="Tu número de teléfono",
        hint_text="569XXXXXXXX",
        width=300,
        keyboard_type=ft.KeyboardType.PHONE
    )

    async def save_config(e):
        if phone_input.value and len(phone_input.value) >= 9:
            state["phone"] = phone_input.value
            try:
                if hasattr(page, "client_storage") and page.client_storage is not None:
                    page.client_storage.set("user_phone", phone_input.value)
            except: pass
            await show_main_view()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Ingresa un número válido"))
            page.snack_bar.open = True
            page.update()

    async def show_main_view():
        page.controls.clear()
        phone = state["phone"] or "No configurado"
        page.add(
            ft.Text("SISTEMA DE SEGURIDAD", size=14, weight="bold", opacity=0.6),
            ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
            panic_button,
            ft.Divider(height=60, color=ft.Colors.TRANSPARENT),
            ft.Text(f"📞 {phone}", size=16, opacity=0.8),
            ft.ElevatedButton(
                "REARMAR SISTEMA", 
                icon=ft.Icons.REFRESH, 
                on_click=send_reset_alert,
                style=ft.ButtonStyle(color=ft.Colors.BLUE_400)
            ),
            ft.TextButton("Cambiar número", on_click=reset_config),
        )
        page.update()

    async def reset_config(e):
        state["phone"] = None
        try:
            if hasattr(page, "client_storage") and page.client_storage is not None:
                page.client_storage.clear()
        except: pass
        page.controls.clear()
        page.add(onboarding_view)
        page.update()

    onboarding_view = ft.Column(
        [
            ft.Icon(ft.Icons.SECURITY, size=100, color=ft.Colors.BLUE_400),
            ft.Text("Configuración", size=24, weight="bold"),
            phone_input,
            ft.FilledButton("GUARDAR", on_click=save_config, width=300),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    if state["phone"]:
        await show_main_view()
    else:
        page.add(onboarding_view)

if __name__ == "__main__":
    ft.app(main)