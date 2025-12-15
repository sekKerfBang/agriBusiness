from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

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
        self.items.append({
            "product_id": product_id,
            "quantity": quantity,
            "price": price,
            "name": name
        })
    
    def clear(self):
        self.items.clear()
    
    @property
    def total(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items)

class AppState:
    def __init__(self):
        self.user = UserState()
        self.cart = CartState()
        self.products: List[Dict] = []
        self.orders: List[Dict] = []
        self.current_producer: Optional[Dict] = None
    
    def reset(self):
        self.user = UserState()
        self.cart.clear()
        self.products = []
        self.orders = []


# from dataclasses import dataclass, field
# from typing import Optional, List, Dict, Any
# from pydantic import BaseModel

# @dataclass
# class UserState:
#     """État utilisateur"""
#     is_authenticated: bool = False
#     token: Optional[str] = None
#     user_data: Optional[Dict] = None
#     role: Optional[str] = None

# @dataclass
# class CartState:
#     """État du panier"""
#     items: List[Dict] = field(default_factory=list)
    
#     def add_item(self, product_id: int, quantity: int, price: float, name: str):
#         self.items.append({
#             "product_id": product_id,
#             "quantity": quantity,
#             "price": price,
#             "name": name
#         })
    
#     @property
#     def total(self) -> float:
#         return sum(item["price"] * item["quantity"] for item in self.items)

# class AppState:
#     """État global de l'application"""
#     def __init__(self):
#         self.user = UserState()
#         self.cart = CartState()
#         self.products: List[Dict] = []
#         self.orders: List[Dict] = []
    
#     def reset(self):
#         """Réinitialise l'état (déconnexion)"""
#         self.user = UserState()
#         self.cart = CartState()
#         self.products = []
#         self.orders = []