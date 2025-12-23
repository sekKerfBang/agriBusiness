import flet as ft

def CartItemCard(item, on_remove, on_update_quantity):
    quantity = item.get('quantity', 1)
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text(item.get('name', 'Produit'), weight=ft.FontWeight.BOLD),
                ft.Text(f"{quantity} x {item.get('price', 0)}€"),
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: on_update_quantity(item['product_id'], quantity - 1)),
                    ft.Text(str(quantity)),
                    ft.IconButton(ft.Icons.ADD, on_click=lambda e: on_update_quantity(item['product_id'], quantity + 1)),
                    ft.IconButton(ft.Icons.DELETE, on_click=lambda e: on_remove(item['product_id'])),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True),
            ]),
            padding=15,
        ),
        elevation=3,
    )



# import flet as ft

# def CartItemCard(item, on_remove, on_update_quantity):
#     """Carte pour un article dans le panier"""
#     return ft.Card(
#         content=ft.Container(
#             content=ft.Column([
#                 ft.ListTile(
#                     title=ft.Text(item.get('product_name', 'Produit')),
#                     subtitle=ft.Text(f"{item.get('quantity', 1)} x {item.get('unit_price', 0)}€"),
#                 ),
#                 ft.Row([
#                     ft.IconButton(ft.icons.REMOVE, on_click=lambda e: on_update_quantity(item['id'], item['quantity'] - 1)),
#                     ft.Text(str(item.get('quantity', 1))),
#                     ft.IconButton(ft.icons.ADD, on_click=lambda e: on_update_quantity(item['id'], item['quantity'] + 1)),
#                     ft.IconButton(ft.icons.DELETE, on_click=lambda e: on_remove(item['id'])),
#                 ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
#             ]),
#             padding=10,
#         )
#     )