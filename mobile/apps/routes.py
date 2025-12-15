import flet as ft
from views.auth_view import AuthView
from views.marketplace_view import MarketplaceView
from views.card_view import CartView
from views.orders_view import OrdersView
from views.dashboard_view import DashboardView

class Routes:
    def __init__(self, page: ft.Page, state, api):
        self.page = page
        self.state = state
        self.api = api
    
    def handle_route(self, route):
        """Gère les changements de route"""
        route = route.route if hasattr(route, 'route') else route
        
        # Nettoie la vue précédente
        self.page.views.clear()
        
        if route == "/" or route == "/auth":
            self.page.views.append(AuthView(self.state, self.api, self.on_login_success))
        
        elif route == "/marketplace":
            if not self.state.user.is_authenticated:
                self.page.go("/auth")
                return
            view = MarketplaceView(self.state, self.api)
            self.page.views.append(view)
            self.page.run_task(view.load_products)
        
        elif route == "/cart":
            if not self.state.user.is_authenticated:
                self.page.go("/auth")
                return
            view = CartView(self.state, self.api)
            self.page.views.append(view)
            self.page.run_task(view.load_cart)
        
        elif route == "/orders":
            if not self.state.user.is_authenticated:
                self.page.go("/auth")
                return
            view = OrdersView(self.state, self.api)
            self.page.views.append(view)
            self.page.run_task(view.load_orders)
        
        elif route == "/dashboard":
            if not self.state.user.is_authenticated or self.state.user.role != 'PRODUCTEUR':
                self.page.go("/marketplace")
                return
            view = DashboardView(self.state, self.api)
            self.page.views.append(view)
            self.page.run_task(view.load_stats)
        
        self.page.update()
    
    def handle_view_pop(self, view):
        """Gère le retour en arrière"""
        if len(self.page.views) > 1:
            self.page.views.pop()
            top_view = self.page.views[-1]
            self.page.go(top_view.route)
    
    def on_login_success(self):
        """Callback après login réussi"""
        self.page.go("/marketplace")