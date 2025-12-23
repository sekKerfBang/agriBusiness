import flet as ft

class DashboardView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/dashboard")
        self.state = state
        self.api = api
        
        self.stats_grid = ft.ResponsiveRow(spacing=10)
        self.loading = ft.ProgressRing(visible=False)
        
        self.controls = [
            ft.AppBar(
                title=ft.Text("Dashboard Producteur"),
                bgcolor=ft.Colors.GREEN,
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/marketplace")
                ),
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        on_click=self.logout,
                        tooltip="Déconnexion"
                    )
                ]
            ),
            ft.Container(
                content=ft.Column([
                    self.loading,
                    ft.Text("📊 Statistiques", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    self.stats_grid,
                    ft.ElevatedButton(
                        "Gérer mes produits",
                        on_click=lambda _: self.page.show_snack_bar(ft.SnackBar(content=ft.Text("À implémenter"))),
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                        expand=True,
                    ),
                ], spacing=20),
                padding=20,
                expand=True,
            )
        ]
    
    async def load_stats(self):
        self.loading.visible = True
        self.update()
        
        stats = await self.api.get_stats()
        
        if stats:
            self.stats_grid.controls = [
                ft.Column(span=12 if self.page.window_width < 600 else 6, controls=[
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(key, size=16, color=ft.Colors.GREY),
                                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ]),
                            padding=20,
                        ),
                        elevation=4,
                    )
                ]) for key, value in stats.items()
            ]
        
        self.loading.visible = False
        self.update()
    
    async def logout(self, e):
        self.state.reset()
        self.page.go("/auth")



# import flet as ft

# class DashboardView(ft.View):
#     def __init__(self, state, api):
#         super().__init__(route="/dashboard")
#         self.state = state
#         self.api = api
        
#         self.stats_text = ft.Text("Chargement...", size=16)
        
#         self.controls = [
#             ft.AppBar(
#                 title=ft.Text("Dashboard Producteur"),
#                 bgcolor=ft.colors.GREEN,
#                 leading=ft.IconButton(
#                     icon=ft.icons.ARROW_BACK,
#                     on_click=lambda _: self.page.go("/marketplace")
#                 ),
#                 actions=[
#                     ft.IconButton(
#                         icon=ft.icons.LOGOUT,
#                         on_click=self.logout,
#                         tooltip="Déconnexion"
#                     )
#                 ]
#             ),
#             ft.Container(
#                 content=ft.Column([
#                     ft.Text("📊 Statistiques", size=24, weight=ft.FontWeight.BOLD),
#                     self.stats_text,
#                     ft.ElevatedButton(
#                         "Gérer mes produits",
#                         on_click=lambda _: self.page.show_snack_bar(ft.SnackBar(content=ft.Text("À implémenter"))),
#                         bgcolor=ft.colors.BLUE,
#                         color=ft.colors.WHITE,
#                         width=300,
#                     ),
#                 ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
#                 padding=20,
#                 expand=True,
#             )
#         ]
    
#     async def load_stats(self):
#         """Charge les stats du producteur"""
#         # TODO: Implémenter l'endpoint API /dashboard/stats/
#         self.stats_text.value = """
#         Produits: 12
#         Commandes: 5
#         Chiffre d'affaires: 234.56€
#         """
#         self.update()
    
#     def logout(self, e):
#         """Déconnexion"""
#         self.state.reset()
#         self.page.client_storage.remove("auth_token")
#         self.page.go("/auth")