import flet as ft

class DashboardView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/dashboard")
        self.state = state
        self.api = api
        
        self.stats_text = ft.Text("Chargement...", size=16)
        
        self.controls = [
            ft.AppBar(
                title=ft.Text("Dashboard Producteur"),
                bgcolor=ft.colors.GREEN,
                leading=ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/marketplace")
                ),
                actions=[
                    ft.IconButton(
                        icon=ft.icons.LOGOUT,
                        on_click=self.logout,
                        tooltip="Déconnexion"
                    )
                ]
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("📊 Statistiques", size=24, weight=ft.FontWeight.BOLD),
                    self.stats_text,
                    ft.ElevatedButton(
                        "Gérer mes produits",
                        on_click=lambda _: self.page.show_snack_bar(ft.SnackBar(content=ft.Text("À implémenter"))),
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                        width=300,
                    ),
                ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                expand=True,
            )
        ]
    
    async def load_stats(self):
        """Charge les stats du producteur"""
        # TODO: Implémenter l'endpoint API /dashboard/stats/
        self.stats_text.value = """
        Produits: 12
        Commandes: 5
        Chiffre d'affaires: 234.56€
        """
        self.update()
    
    def logout(self, e):
        """Déconnexion"""
        self.state.reset()
        self.page.client_storage.remove("auth_token")
        self.page.go("/auth")