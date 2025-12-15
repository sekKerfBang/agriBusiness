import flet as ft

def ProductCard(product, on_add_to_cart, on_view_detail):
    """Composant carte produit réutilisable"""
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Image(
                    src=product.get("image", "https://via.placeholder.com/300"),
                    height=150,
                    fit=ft.ImageFit.COVER,
                ),
                ft.ListTile(
                    title=ft.Text(product["name"], weight=ft.FontWeight.BOLD),
                    subtitle=ft.Column([
                        ft.Text(product.get("producer_name", "Inconnu"), size=12),
                        ft.Text(f"{product['price']}€ / {product['unit']}", size=14, color=ft.colors.GREEN),
                        ft.Text(f"Stock: {product['stock']}", size=10, color=ft.colors.GREY),
                    ], spacing=2),
                ),
                ft.Row([
                    ft.TextButton(
                        "Voir détails",
                        on_click=lambda e: on_view_detail(product),
                    ),
                    ft.ElevatedButton(
                        "Ajouter",
                        on_click=lambda e: on_add_to_cart(product),
                        bgcolor=ft.colors.GREEN,
                        color=ft.colors.WHITE,
                        height=35,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=10,
        ),
        elevation=2,
    )