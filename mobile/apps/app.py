import flet as ft
from .state import AppState
from .services.api_client import APIClient
from .routes import Routes

class AgriMarketApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.state = AppState()
        self.api = APIClient()
        self.routes = Routes(self.page, self.state, self.api)
        
        self.configure_page()
        self.setup_routes()
        
    def configure_page(self):
        """Configuration initiale de la page"""
        self.page.title = "AgriMarket"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.window_width = 400
        self.page.window_height = 800
        
    def setup_routes(self):
        """Configuration du routing"""
        self.page.on_route_change = self.routes.handle_route
        self.page.on_view_pop = self.routes.handle_view_pop
        self.page.go("/")
    
    def run(self):
        """Lance l'application"""
        self.page.update()