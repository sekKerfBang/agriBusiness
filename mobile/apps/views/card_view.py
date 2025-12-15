import flet as ft
from apps.components.cart_item_card import CartItemCard

class CartView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/cart")
        self.state = state
        self.api = api
        
        self.cart_items = ft.ListView(expand=True, spacing=10)
        self.total_text = ft.Text("Total: 0.00€", size=20, weight=ft.FontWeight.BOLD)
        
        self.controls = [
            ft.AppBar(
                title=ft.Text("Mon Panier"),
                bgcolor=ft.colors.GREEN,
                leading=ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda _: self.page.go("/marketplace")
                )
            ),
            ft.Container(
                content=ft.Column([
                    self.cart_items,
                    ft.Divider(),
                    self.total_text,
                    ft.ElevatedButton(
                        "Passer la commande",
                        on_click=self.checkout,
                        width=300,
                        bgcolor=ft.colors.GREEN,
                        color=ft.colors.WHITE,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                expand=True,
            )
        ]
    
    async def load_cart(self):
        """Charge le contenu du panier"""
        self.cart_items.controls.clear()
        
        # Charger depuis l'API si utilisateur connecté
        cart_data = await self.api.get_cart()
        
        if cart_data and 'items' in cart_data:
            for item in cart_data['items']:
                self.cart_items.controls.append(
                    CartItemCard(item, self.remove_item, self.update_quantity)
                )
        else:
            # Afficher le panier local
            for item in self.state.cart.items:
                self.cart_items.controls.append(
                    ft.ListTile(
                        title=ft.Text(item['name']),
                        subtitle=ft.Text(f"{item['quantity']} x {item['price']}€"),
                    )
                )
        
        self.update_total()
        self.update()
    
    def update_total(self):
        total = sum(item['price'] * item['quantity'] for item in self.state.cart.items)
        self.total_text.value = f"Total: {total:.2f}€"
    
    async def remove_item(self, item_id):
        """Retire un article du panier"""
        # Implémentation API
        self.state.cart.items = [item for item in self.state.cart.items if item['product_id'] != item_id]
        await self.load_cart()
    
    async def update_quantity(self, item_id, quantity):
        """Met à jour la quantité"""
        for item in self.state.cart.items:
            if item['product_id'] == item_id:
                item['quantity'] = quantity
                break
        await self.load_cart()
    
    async def checkout(self, e):
        """Passe à la commande"""
        if not self.state.cart.items:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Panier vide !")))
            return
        
        self.page.go("/checkout")