import flet as ft
import logging
from apps.components.product_card import ProductCard

logger = logging.getLogger(__name__)


class MarketplaceView(ft.View):
    def __init__(self, state, api):
        super().__init__(route="/marketplace")
        self.state = state
        self.api = api

        self.search_field = ft.TextField(
            label="Rechercher des produits",
            on_submit=self.handle_search,
            border_radius=12,
            expand=True,
        )

        self.products_grid = ft.ResponsiveRow(
            spacing=15,
            run_spacing=15,
        )

        self.loading = ft.ProgressRing(visible=True)

        self.controls = [
            ft.AppBar(
                title=ft.Text("Marché AgroBusiness"),
                bgcolor=ft.Colors.GREEN_700,
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.SHOPPING_CART,
                        tooltip="Panier",
                        on_click=self.show_cart,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PERSON,
                        tooltip="Profil",
                        on_click=self.show_profile,
                    ),
                ],
            ),
            ft.Container(
                padding=15,
                expand=True,
                content=ft.Column(
                    spacing=20,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        self.search_field,
                        self.loading,
                        self.products_grid,
                    ],
                ),
            ),
        ]

    # ==============================
    # Lifecycle
    # ==============================
    def did_mount(self):
        self.page.run_task(self.load_products)

    # ==============================
    # Data loading
    # ==============================
    async def load_products(self):
        self.loading.visible = True
        self.products_grid.controls.clear()
        self.update()

        try:
            products = await self.api.get_products()
            page_width = self.page.width or 800  # fallback SAFE

            if not products:
                self.products_grid.controls.append(
                    ft.Text(
                        "Aucun produit disponible",
                        color=ft.Colors.GREY,
                        size=16,
                    )
                )
            else:
                for product in products:
                    self.products_grid.controls.append(
                        ft.Container(
                            col={"xs": 12, "sm": 6, "md": 4, "lg": 3},
                            content=ProductCard(
                                product=product,
                                page_width=page_width,
                                on_add_to_cart=self.add_to_cart,
                                on_view_detail=self.view_product_detail,
                            ),
                        )
                    )

        except Exception as e:
            logger.error(f"Erreur critique load_products : {e}")
            self.products_grid.controls.append(
                ft.Text(
                    "Erreur de chargement des produits",
                    color=ft.Colors.RED,
                )
            )

        self.loading.visible = False
        self.update()

    # ==============================
    # Actions
    # ==============================
    async def handle_search(self, e):
        if self.search_field.value.strip():
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Recherche en cours…")
            )
            self.page.snack_bar.open = True
            self.page.update()

    def add_to_cart(self, product):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"{product.get('name')} ajouté au panier"),
            bgcolor=ft.Colors.GREEN,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def view_product_detail(self, product):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(product.get("name", "")),
            content=ft.Text(product.get("description", "Pas de description")),
            actions=[
                ft.TextButton("Fermer", on_click=lambda e: self.close_dialog()),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def close_dialog(self):
        self.page.dialog.open = False
        self.page.update()

    def show_cart(self, e):
        self.page.go("/cart")   

    def show_profile(self, e):
        self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Profil à implémenter")))
    
            