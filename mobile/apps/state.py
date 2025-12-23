from dataclasses import dataclass, field
from typing import Optional, List, Dict
import flet as ft 

@dataclass
class UserState:
    is_authenticated: bool = False
    token: Optional[str] = None
    user_data: Optional[Dict] = None
    role: Optional[str] = None

@dataclass
class CartState:
    items: List[Dict] = field(default_factory=list)
    
    def add_item(self, product_id: int, quantity: int, price: float, name: str):
        for item in self.items:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                return
        self.items.append({
            "product_id": product_id,
            "quantity": quantity,
            "price": price,
            "name": name
        })
    
    def remove_item(self, product_id: int):
        self.items = [item for item in self.items if item["product_id"] != product_id]
    
    def update_quantity(self, product_id: int, quantity: int):
        for item in self.items:
            if item["product_id"] == product_id:
                item["quantity"] = max(1, quantity)
                break
    
    def clear(self):
        self.items.clear()
    
    @property
    def total(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items)

class AppState:
    def __init__(self, page: Optional[ft.Page] = None):
        self.user = UserState()
        self.cart = CartState()
        self.products: List[Dict] = []
        self.orders: List[Dict] = []
        self.current_producer: Optional[Dict] = None
        self.page = page  # Pour storage
    
    async def load_from_storage(self):
        if self.page:
            token = await self.page.client_storage.get_async("auth_token")
            if token:
                self.user.token = token
                self.user.is_authenticated = True
            # Load cart if needed (JSON serialize)
    
    async def save_to_storage(self):
        if self.page:
            if self.user.token:
                await self.page.client_storage.set_async("auth_token", self.user.token)
    
    def reset(self):
        self.user = UserState()
        self.cart.clear()
        self.products = []
        self.orders = []
        if self.page:
            self.page.client_storage.remove("auth_token")

# from dataclasses import dataclass, field
# from typing import Optional, List, Dict, Any

# @dataclass
# class UserState:
#     is_authenticated: bool = False
#     token: Optional[str] = None
#     user_data: Optional[Dict] = None
#     role: Optional[str] = None

# @dataclass
# class CartState:
#     items: List[Dict] = field(default_factory=list)
    
#     def add_item(self, product_id: int, quantity: int, price: float, name: str):
#         self.items.append({
#             "product_id": product_id,
#             "quantity": quantity,
#             "price": price,
#             "name": name
#         })
    
#     def clear(self):
#         self.items.clear()
    
#     @property
#     def total(self) -> float:
#         return sum(item["price"] * item["quantity"] for item in self.items)

# class AppState:
#     def __init__(self):
#         self.user = UserState()
#         self.cart = CartState()
#         self.products: List[Dict] = []
#         self.orders: List[Dict] = []
#         self.current_producer: Optional[Dict] = None
    
#     def reset(self):
#         self.user = UserState()
#         self.cart.clear()
#         self.products = []
#         self.orders = []


# # from dataclasses import dataclass, field
# # from typing import Optional, List, Dict, Any
# # from pydantic import BaseModel

# # @dataclass
# # class UserState:
# #     """État utilisateur"""
# #     is_authenticated: bool = False
# #     token: Optional[str] = None
# #     user_data: Optional[Dict] = None
# #     role: Optional[str] = None

# # @dataclass
# # class CartState:
# #     """État du panier"""
# #     items: List[Dict] = field(default_factory=list)
    
# #     def add_item(self, product_id: int, quantity: int, price: float, name: str):
# #         self.items.append({
# #             "product_id": product_id,
# #             "quantity": quantity,
# #             "price": price,
# #             "name": name
# #         })
    
# #     @property
# #     def total(self) -> float:
# #         return sum(item["price"] * item["quantity"] for item in self.items)

# # class AppState:
# #     """État global de l'application"""
# #     def __init__(self):
# #         self.user = UserState()
# #         self.cart = CartState()
# #         self.products: List[Dict] = []
# #         self.orders: List[Dict] = []
    
# #     def reset(self):
# #         """Réinitialise l'état (déconnexion)"""
# #         self.user = UserState()
# #         self.cart = CartState()
# #         self.products = []
# #         self.orders = []