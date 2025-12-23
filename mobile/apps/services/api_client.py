import httpx
from typing import Optional, Dict, List, Any
import logging
import time

logger = logging.getLogger(__name__)

class APIClient:
    """
    Client HTTP asynchrone pour communiquer avec l'API Django (DRF + simplejwt).
    Gère l'authentification JWT, les retries, et les erreurs.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/"):
        self.base_url = base_url.rstrip("/") + "/"  # Normalise l'URL
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def set_token(self, token: str):
        """Définit le token JWT pour les requêtes authentifiées"""
        self.token = token
    
    @property
    def headers(self) -> Dict[str, str]:
        """Headers par défaut avec Content-Type JSON et Authorization si token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _request(self, method: str, endpoint: str, retries: int = 3, **kwargs) -> Any:
        """
        Requête HTTP avec retry exponentiel et gestion d'erreurs détaillée
        """
        url = self.base_url + endpoint.lstrip("/")
        
        for attempt in range(1, retries + 1):
            try:
                response = await self.client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else None
                
            except httpx.HTTPStatusError as e:
                error_detail = await e.response.text()
                logger.error(f"HTTP {e.response.status_code} sur {url} (tentative {attempt}/{retries}): {error_detail}")
                if attempt == retries:
                    raise
            except httpx.RequestError as e:
                logger.error(f"Erreur réseau sur {url} (tentative {attempt}/{retries}): {e}")
                if attempt == retries:
                    raise
            # Backoff exponentiel
            if attempt < retries:
                await time.sleep(1 * (2 ** (attempt - 1)))
    
    # ========================
    # Méthodes publiques
    # ========================
    
    async def login(self, username: str, password: str) -> Optional[Dict]:
        """Connexion et récupération du token JWT"""
        try:
            data = await self._request(
                "POST",
                "users/token/",
                json={"username": username, "password": password}  # json= obligatoire pour simplejwt
            )
            if data and "access" in data:
                self.set_token(data["access"])
                logger.info(f"Login réussi pour {username}")
            return data
        except Exception as e:
            logger.error(f"Échec login : {e}")
            return None
    
    async def get_products(self, category: Optional[int] = None) -> List[Dict]:
        """Récupère la liste des produits depuis l'API"""
        params = {"category": category} if category else {}
        try:
            response = await self.client.get(
                f"{self.base_url}products/",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            # Force le parsing JSON
            data = response.json()
            
            # Log pour debug
            logger.info(f"Produits reçus : {type(data)} - {len(data) if isinstance(data, list) else data}")
            
            # Retourne une liste vide si pas list
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'results' in data:  # Pagination DRF
                return data['results']
            else:
                logger.warning(f"Format inattendu de l'API products : {data}")
                return []
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {await e.response.text()}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Erreur réseau : {e}")
            return []
        except ValueError as e:  # JSON decode error
            logger.error(f"Erreur parsing JSON : {e} - Contenu : {await response.text()}")
            return []
    

    async def get_cart(self) -> Optional[Dict]:
        try:
            response = await self.client.get(f"{self.base_url}orders/cart/", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erreur get_cart : {e}")
            return None
    
    async def add_to_cart(self, product_id: int, quantity: int = 1) -> bool:
        """Ajoute un produit au panier"""
        try:
            await self._request(
                "POST",
                "orders/cart/add/",
                json={"product_id": product_id, "quantity": quantity}
            )
            return True
        except Exception as e:
            logger.error(f"Erreur add_to_cart : {e}")
            return False
    
    async def create_order(self, items: List[Dict], shipping_address: str) -> Optional[Dict]:
        """Crée une commande"""
        try:
            data = {
                "items": items,
                "shipping_address": shipping_address,
            }
            return await self._request("POST", "orders/", json=data)
        except Exception as e:
            logger.error(f"Erreur create_order : {e}")
            return None
    
    async def get_orders(self) -> List[Dict]:
        """Récupère les commandes de l'utilisateur"""
        try:
            return await self._request("GET", "orders/") or []
        except Exception as e:
            logger.error(f"Erreur get_orders : {e}")
            return []
    
    async def get_stats(self) -> Dict:
        """Récupère les stats du producteur"""
        try:
            return await self._request("GET", "dashboard/stats/") or {}
        except Exception as e:
            logger.error(f"Erreur get_stats : {e}")
            return {}
    
    async def close(self):
        """Ferme proprement le client HTTP"""
        await self.client.aclose()



# import httpx
# from typing import Optional, Dict, List
# import logging
# import time

# logger = logging.getLogger(__name__)

# class APIClient:
#     def __init__(self, base_url: str = "http://127.0.0.1:8000/api/"):
#         self.base_url = base_url
#         self.token: Optional[str] = None
#         self.client = httpx.AsyncClient(timeout=30.0)
    
#     def set_token(self, token: str):
#         self.token = token
    
#     @property
#     def headers(self) -> Dict[str, str]:
#         headers = {"Content-Type": "application/json"}
#         if self.token:
#             headers["Authorization"] = f"Bearer {self.token}"
#         return headers
    
#     async def _request_with_retry(self, method: str, url: str, retries: int = 3, **kwargs):
#         for attempt in range(retries):
#             try:
#                 response = await self.client.request(method, url, headers=self.headers, **kwargs)
#                 response.raise_for_status()
#                 return response.json()
#             except httpx.HTTPError as e:
#                 if attempt == retries - 1:
#                     logger.error(f"API error after {retries} attempts: {e}")
#                     raise
#                 time.sleep(1 * (2 ** attempt))  # Exponential backoff
    
#     async def login(self, username: str, password: str) -> Optional[Dict]:
#         return await self._request_with_retry("POST", f"{self.base_url}users/token/", data={"username": username, "password": password})
    
#     async def get_products(self, category: Optional[int] = None) -> List[Dict]:
#         params = {"category": category} if category else {}
#         return await self._request_with_retry("GET", f"{self.base_url}products/", params=params)
    
#     async def get_cart(self) -> Optional[Dict]:
#         return await self._request_with_retry("GET", f"{self.base_url}orders/cart/")
    
#     async def add_to_cart(self, product_id: int, quantity: int) -> bool:
#         data = {"product_id": product_id, "quantity": quantity}
#         response = await self._request_with_retry("POST", f"{self.base_url}orders/cart/add/", json=data)
#         return bool(response)
    
#     async def create_order(self, items: List[Dict], shipping_address: str) -> Optional[Dict]:
#         data = {
#             "items": items,
#             "shipping_address": shipping_address,
#             "total_amount": sum(item["price"] * item["quantity"] for item in items)
#         }
#         return await self._request_with_retry("POST", f"{self.base_url}orders/", json=data)
    
#     async def get_orders(self) -> List[Dict]:
#         return await self._request_with_retry("GET", f"{self.base_url}orders/")
    
#     async def get_stats(self) -> Dict:
#         return await self._request_with_retry("GET", f"{self.base_url}dashboard/stats/")
    
#     async def close(self):
#         await self.client.aclose()
