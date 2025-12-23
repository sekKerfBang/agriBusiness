import flet as ft


def ProductCard(product, page_width, on_add_to_cart, on_view_detail):
    image_height = 180 if page_width >= 600 else 140

    return ft.Card(
        elevation=4,
        content=ft.Container(
            padding=10,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Image(
                        src=product.get("images", "https://via.placeholder.com/300"),
                        height=image_height,
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.BorderRadius(
                            top_left=12,
                            top_right=12,
                            bottom_left=0,
                            bottom_right=0,
                        ),
                    ),
                    ft.Text(
                        product.get("name", "Produit"),
                        weight=ft.FontWeight.BOLD,
                        size=16,
                    ),
                    ft.Text(
                        f"{product.get('price', 0)} € / {product.get('unit', '')}",
                        color=ft.Colors.GREEN,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.TextButton(
                                "Détails",
                                on_click=lambda e: on_view_detail(product),
                            ),
                            ft.ElevatedButton(
                                "Ajouter",
                                bgcolor=ft.Colors.GREEN,
                                color=ft.Colors.WHITE,
                                on_click=lambda e: on_add_to_cart(product),
                            ),
                        ],
                    ),
                ],
            ),
        ),
    )


