import flet as ft

class OrdersView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/orders")
        self.state = state
        self.api = api
        
        self.orders_list = ft.ResponsiveRow(spacing=10)
        self.loading = ft.ProgressRing(visible=True)
        
        self.controls = [
            ft.AppBar(
                title=ft.Text("Mes Commandes"),
                bgcolor=ft.Colors.GREEN,
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/marketplace")
                )
            ),
            ft.Container(
                content=ft.Column([
                    self.loading,
                    self.orders_list,
                ]),
                padding=10,
                expand=True,
            )
        ]
    
    async def load_orders(self):
        self.loading.visible = True
        self.update()
        
        self.orders_list.controls.clear()
        
        orders = await self.api.get_orders()
        
        col_span = 12 if self.page.window_width < 600 else 6
        for order in orders:
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Commande #{order['order_number']}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Date: {order['created_at']}"),
                        ft.Text(f"Total: {order['total_amount']}€"),
                        ft.Text(f"Statut: {order['status']}", color=ft.Colors.GREEN if order['status'] == 'DELIVERED' else ft.Colors.RED),
                    ]),
                    padding=15,
                ),
                elevation=4,
            )
            self.orders_list.controls.append(ft.Column(span=col_span, controls=[card]))
        
        self.loading.visible = False
        self.update()

