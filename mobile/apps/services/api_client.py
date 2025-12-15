import httpx
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str = "http://192.168.1.100:8000/api/"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def set_token(self, token: str):
        self.token = token
    
    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    async def login(self, username: str, password: str) -> Optional[Dict]:
        """Login et récupération du token"""
        try:
            response = await self.client.post(
                f"{self.base_url}users/token/",
                data={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            self.set_token(data["access"])
            return data
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return None
    
    async def get_products(self, category: Optional[int] = None) -> List[Dict]:
        """Récupère la liste des produits"""
        try:
            params = {}
            if category:
                params["category"] = category
            
            response = await self.client.get(
                f"{self.base_url}products/",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Get products failed: {e}")
            return []
    
    async def get_cart(self) -> Optional[Dict]:
        """Récupère le panier de l'utilisateur"""
        try:
            response = await self.client.get(
                f"{self.base_url}orders/cart/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Get cart failed: {e}")
            return None
    
    async def add_to_cart(self, product_id: int, quantity: int) -> bool:
        """Ajoute un produit au panier"""
        try:
            response = await self.client.post(
                f"{self.base_url}orders/cart/add/",
                headers=self.headers,
                data={"product_id": product_id, "quantity": quantity}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Add to cart failed: {e}")
            return False
    
    async def create_order(self, items: List[Dict], shipping_address: str) -> Optional[Dict]:
        """Crée une commande"""
        try:
            data = {
                "items": items,
                "shipping_address": shipping_address,
                "total_amount": sum(item["price"] * item["quantity"] for item in items)
            }
            response = await self.client.post(
                f"{self.base_url}orders/",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Create order failed: {e}")
            return None
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()


# import httpx
# from typing import Optional, Dict, Any
# from functools import wraps, partial
# import logging  

# logger = logging.getLogger(__name__)

# # Partial pour créer des endpoints
# api_endpoint = partial(lambda base, endpoint: f"{base}{endpoint}", 
#                       base="http://192.168.1.100:8000/api/")

# def require_auth(func):
#     """Décorateur pour nécessiter l'authentification"""
#     @wraps(func)
#     def wrapper(self, *args, **kwargs):
#         if not self.token:
#             raise ValueError("Authentication required")
#         return func(self, *args, **kwargs)
#     return wrapper

# class APIClient:
#     """Client API avec support async"""
#     def __init__(self):
#         self.token: Optional[str] = None
#         self.client = httpx.AsyncClient(timeout=30.0)
    
#     def set_token(self, token: str):
#         self.token = token
    
#     @property
#     def headers(self) -> Dict[str, str]:
#         return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
#     async def login(self, username: str, password: str) -> Optional[Dict]:
#         """Login et récupération token"""
#         try:
#             response = await self.client.post(
#                 api_endpoint("users/token/"),
#                 data={"username": username, "password": password}
#             )
#             response.raise_for_status()
#             data = response.json()
#             self.set_token(data["access"])
#             return data
#         except Exception as e:
#             logger.error(f"Login failed: {e}")
#             return None
    
#     @require_auth
#     async def get_products(self) -> list:
#         """Récupère la liste des produits"""
#         try:
#             response = await self.client.get(
#                 api_endpoint("products/"),
#                 headers=self.headers
#             )
#             response.raise_for_status()
#             return response.json()
#         except Exception as e:
#             logger.error(f"Get products failed: {e}")
#             return []
    
#     @require_auth
#     async def create_order(self, items: list, shipping_address: str) -> Optional[Dict]:
#         """Crée une commande"""
#         try:
#             data = {
#                 "items": items,
#                 "shipping_address": shipping_address,
#                 "total_amount": sum(item["price"] * item["quantity"] for item in items)
#             }
#             response = await self.client.post(
#                 api_endpoint("orders/"),
#                 json=data,
#                 headers=self.headers
#             )
#             response.raise_for_status()
#             return response.json()
#         except Exception as e:
#             logger.error(f"Create order failed: {e}")
#             return None
    
#     async def close(self):
#         """Ferme le client HTTP"""
#         await self.client.aclose()