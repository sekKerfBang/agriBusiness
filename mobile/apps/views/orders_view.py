import flet as ft

class OrdersView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/orders")
        self.state = state
        self.api = api
        
        self.orders_list = ft.ListView(expand=True, spacing=10)
        
        self.controls = [
            ft.AppBar(
                title=ft.Text("Mes Commandes"),
                bgcolor=ft.colors.GREEN,
                leading=ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/marketplace")
                )
            ),
            ft.Container(
                content=self.orders_list,
                padding=10,
                expand=True,
            )
        ]
    
    async def load_orders(self):
        """Charge les commandes de l'utilisateur"""
        self.orders_list.controls.clear()
        
        # TODO: Implémenter l'endpoint API /orders/
        # orders = await self.api.get_orders()
        
        # Simulation pour l'instant
        self.orders_list.controls.append(
            ft.ListTile(
                title=ft.Text("Commande #12345"),
                subtitle=ft.Text("Statut: Livrée - Total: 45.99€"),
            )
        )
        
        self.update()