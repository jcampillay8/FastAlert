import flet as ft
import httpx
import asyncio

# --- CONFIGURACIÓN ---
API_BASE_URL = "http://192.168.100.32:8000/alarma/activar"

async def main(page: ft.Page):
    page.title = "FastAlert - Botón de Pánico"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- VARIABLE DE SESIÓN (Memoria) ---
    state = {"phone": None}

    # Intentar recuperar el teléfono al iniciar
    try:
        val = page.client_storage.get("user_phone")
        if val:
            state["phone"] = val
    except:
        pass

    # --- LÓGICA DE ALERTA ---
    async def send_panic_alert():
        phone = state["phone"]
        if not phone:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Error: Teléfono no configurado"))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(API_BASE_URL, json={"telefono": phone})
                if response.status_code == 200:
                    page.snack_bar = ft.SnackBar(ft.Text("✅ ALERTA ENVIADA EXITOSAMENTE"), bgcolor=ft.Colors.GREEN_700)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error Servidor: {response.status_code}"), bgcolor=ft.Colors.RED_700)
        except Exception:
            page.snack_bar = ft.SnackBar(ft.Text("🚨 Error de conexión con el servidor"), bgcolor=ft.Colors.ORANGE_900)
        
        page.snack_bar.open = True
        page.update()

    # --- DIÁLOGOS Y COMPONENTES ---

    async def handle_confirm(e):
        confirm_dialog.open = False
        page.update()
        await send_panic_alert()

    async def close_dlg(e):
        confirm_dialog.open = False
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ CONFIRMAR EMERGENCIA"),
        content=ft.Text("¿Estás seguro de que deseas activar la alerta vecinal?"),
        actions=[
            ft.TextButton("SÍ, ACTIVAR", on_click=handle_confirm, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("NO, CANCELAR", on_click=close_dlg),
        ],
    )

    # El diálogo debe estar en el overlay
    page.overlay.append(confirm_dialog)

    async def open_confirmation(e):
        confirm_dialog.open = True
        page.update()

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
        shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.RED_900),
        on_click=open_confirmation,
    )

    # --- VISTA DE CONFIGURACIÓN ---
    phone_input = ft.TextField(
        label="Número de Teléfono",
        hint_text="Ej: 569XXXXXXXX",
        width=300
    )

    async def save_config(e):
        if phone_input.value and len(phone_input.value) >= 9:
            state["phone"] = phone_input.value
            try:
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
            ft.Text(f"Registrado como: {phone}", italic=True, opacity=0.5),
            ft.TextButton("Cambiar número", on_click=reset_config),
        )
        page.update()

    async def reset_config(e):
        state["phone"] = None
        try: page.client_storage.clear()
        except: pass
        page.controls.clear()
        page.add(onboarding_view)
        page.update()

    onboarding_view = ft.Column(
        [
            ft.Icon(ft.Icons.SECURITY, size=100, color=ft.Colors.BLUE_400),
            ft.Text("Bienvenido a FastAlert", size=24, weight="bold"),
            phone_input,
            ft.FilledButton("GUARDAR Y CONTINUAR", on_click=save_config, width=300),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --- INICIO ---
    if state["phone"]:
        await show_main_view()
    else:
        page.add(onboarding_view)

if __name__ == "__main__":
    ft.app(target=main)