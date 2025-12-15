import flet as ft
from apps.components.product_card import ProductCard

class MarketplaceView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/marketplace")
        self.state = state
        self.api = api
        
        self.products_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=300,
            spacing=10,
            run_spacing=10,
        )
        
        self.loading = ft.ProgressRing(visible=False)
        
        self.controls = [
            ft.AppBar(
                title=ft.Text("Marché", size=24),
                bgcolor=ft.colors.GREEN,
                actions=[
                    ft.IconButton(
                        icon=ft.icons.SHOPPING_CART,
                        on_click=self.show_cart,
                        tooltip=f"Panier ({len(self.state.cart.items)})"
                    ),
                    ft.IconButton(
                        icon=ft.icons.PERSON,
                        on_click=self.show_profile,
                        tooltip="Profil"
                    )
                ]
            ),
            ft.Container(
                content=ft.Column([
                    ft.TextField(
                        label="Rechercher des produits",
                        on_submit=self.handle_search,
                        width=400,
                    ),
                    self.loading,
                    self.products_grid,
                ]),
                padding=10,
                expand=True,
            )
        ]
    
    async def load_products(self):
        """Charge les produits depuis l'API"""
        self.loading.visible = True
        self.update()
        
        self.products_grid.controls.clear()
        products = await self.api.get_products()
        
        for product in products:
            card = ProductCard(
                product,
                on_add_to_cart=self.add_to_cart,
                on_view_detail=self.view_product_detail
            )
            self.products_grid.controls.append(card)
        
        self.loading.visible = False
        self.update()
    
    async def handle_search(self, e):
        """Gère la recherche"""
        # À implémenter avec API
        pass
    
    def add_to_cart(self, product):
        """Ajoute un produit au panier"""
        self.state.cart.add_item(
            product_id=product["id"],
            quantity=1,
            price=float(product["price"]),
            name=product["name"]
        )
        
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(f"{product['name']} ajouté au panier !"))
        )
        self.update_action_buttons()
    
    def update_action_buttons(self):
        """Met à jour le compteur du panier"""
        for action in self.appbar.actions:
            if hasattr(action, 'tooltip') and 'Panier' in action.tooltip:
                action.tooltip = f"Panier ({len(self.state.cart.items)})"
    
    def show_cart(self, e):
        self.page.go("/cart")
    
    def show_profile(self, e):
        if self.state.user.role == 'PRODUCTEUR':
            self.page.go("/dashboard")
        else:
            self.page.go("/orders")
    
    def view_product_detail(self, product):
        """Affiche les détails du produit"""
        # À implémenter
        pass



# import flet as ft
# from app.components.product_card import ProductCard
# from app.components.cart_modal import CartModal

# class MarketplaceView(ft.View):
#     def __init__(self, state, api):
#         super().__init__(route="/marketplace")
#         self.state = state
#         self.api = api
#         self.products = ft.GridView(
#             expand=True,
#             runs_count=2,
#             max_extent=300,
#             spacing=10,
#             run_spacing=10,
#         )
#         self.init_ui()
    
#     def init_ui(self):
#         self.controls = [
#             ft.AppBar(
#                 title=ft.Text("Marché", size=24, weight=ft.FontWeight.BOLD),
#                 center_title=True,
#                 bgcolor=ft.colors.GREEN,
#                 actions=[
#                     ft.IconButton(
#                         icon=ft.icons.SHOPPING_CART,
#                         on_click=self.show_cart,
#                         tooltip="Voir le panier"
#                     )
#                 ]
#             ),
#             ft.Container(
#                 content=self.products,
#                 padding=10,
#                 expand=True
#             )
#         ]
    
#     async def load_products(self):
#         """Charge les produits depuis l'API"""
#         products = await self.api.get_products()
#         self.products.controls.clear()
        
#         for product in products:
#             card = ProductCard(product, self.add_to_cart)
#             self.products.controls.append(card)
        
#         self.update()
    
#     def add_to_cart(self, product):
#         """Ajoute un produit au panier"""
#         self.state.cart.add_item(
#             product_id=product["id"],
#             quantity=1,
#             price=float(product["price"]),
#             name=product["name"]
#         )
        
#         # Notification toast
#         self.page.show_snack_bar(
#             ft.SnackBar(content=ft.Text(f"{product['name']} ajouté !"))
#         )
    
#     def show_cart(self, e):
#         """Affiche le modal panier"""
#         modal = CartModal(self.state.cart, self.on_checkout)
#         self.page.dialog = modal
#         modal.open = True
#         self.page.update()
    
#     async def on_checkout(self):
#         """Passe la commande"""
#         if not self.state.cart.items:
#             return
        
#         order = await self.api.create_order(
#             self.state.cart.items,
#             "Adresse du client"  # À récupérer du profil
#         )
        
#         if order:
#             self.state.cart.items.clear()
#             self.page.show_snack_bar(
#                 ft.SnackBar(content=ft.Text("Commande passée avec succès !"))
#             )