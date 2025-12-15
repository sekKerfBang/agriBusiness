import flet as ft
from mobile.apps.app import AgriMarketApp

def main(page: ft.Page):
    """Point d'entrée principal"""
    app = AgriMarketApp(page)
    app.run()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)


# import flet as ft
# from app.routes import Routes
# from app.state import AppState
# from app.services.api_client import APIClient

# class AgriMarketApp:
#     def __init__(self, page: ft.Page):
#         self.page = page
#         self.state = AppState()
#         self.api = APIClient()
          
#         # Configuration page
#         self.page.title = "AgriMarket"
#         self.page.theme_mode = ft.ThemeMode.LIGHT
#         self.page.padding = 0
        
#         # Routes
#         self.routes = Routes(self.page, self.state, self.api)
#         self.page.on_route_change = self.routes.handle_route
        
#         # Route initiale
#         self.page.go("/")
    
#     def main(self):
#         """Point d'entrée principal"""
#         self.page.update()

# def main(page: ft.Page):
#     app = AgriMarketApp(page)
#     app.main()

# if __name__ == "__main__":
#     ft.app(target=main, view=ft.AppView.FLET_APP)
#     # Pour mobile: ft.app(target=main, view=ft.AppView.WEB)