import flet as ft
from apps.state import AppState
from apps.services.api_client import APIClient
from apps.routes import Routes

def main(page: ft.Page):
    """Point d'entrée principal"""
    # Theme global (vert sombre premium)
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.GREEN_700,
            on_primary=ft.Colors.WHITE,
            secondary=ft.Colors.GREEN_300,
            background="#0D1B0A",  
            on_background=ft.Colors.WHITE,
            surface=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
        ),
        visual_density=ft.VisualDensity.ADAPTIVE_PLATFORM_DENSITY,
        use_material3=True,
        font_family="Roboto",
    )
    
    # Init state et API
    state = AppState()
    api = APIClient(base_url="http://127.0.0.1:8000/api/")
    
    # Routes handler
    routes = Routes(page, state, api)
    
    # Listener pour responsive (update on resize)
    def on_resize(e):
        page.update()  # Force refresh pour layouts responsive
    
    page.on_resize = on_resize
    page.on_route_change = routes.handle_route
    
    # Route initiale
    page.go(page.route or "/auth")

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)  # Ou FLET_APP pour mobile