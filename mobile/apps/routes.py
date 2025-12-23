import flet as ft
from apps.views.auth_view import AuthView
from apps.views.marketplace_view import MarketplaceView
from apps.views.card_view import CartView
from apps.views.orders_view import OrdersView
from apps.views.dashboard_view import DashboardView

class Routes:
    def __init__(self, page: ft.Page, state, api):
        self.page = page
        self.state = state
        self.api = api
        self.views_map = {
            "/auth": self._load_auth_view,
            "/marketplace": self._load_marketplace_view,
            "/cart": self._load_cart_view,
            "/orders": self._load_orders_view,
            "/dashboard": self._load_dashboard_view,
        }

    def handle_route(self, e: ft.RouteChangeEvent):
        route = e.route
        self.page.views.clear()

        # Routes publiques
        if route in ("/", "/auth"):
            self._load_auth_view()
        # Routes nécessitant authentification
        elif route in ("/marketplace", "/cart", "/orders", "/dashboard"):
            if not self.state.user.is_authenticated:
                self.page.go("/auth")
                return
            # Accès réservé aux producteurs
            if route == "/dashboard" and self.state.user.role != "PRODUCTEUR":
                self.page.go("/marketplace")
                self._show_snack_bar("Accès réservé aux producteurs", ft.Colors.ORANGE)
                return
            # Chargement dynamique des vues
            self.views_map[route]()
        else:
            # Route inconnue → redirection par défaut
            self.page.go("/marketplace" if self.state.user.is_authenticated else "/auth")

        self.page.update()

    def _show_snack_bar(self, message: str, color=ft.Colors.GREEN):
        """Affiche un snackbar de façon sécurisée."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
        )
        self.page.snack_bar.open = True
        self.page.update()

    # Chargement des vues
    def _load_auth_view(self):
        self.page.views.append(AuthView(self.state, self.api, self.on_login_success))

    def _load_marketplace_view(self):
        self.page.views.append(MarketplaceView(self.state, self.api))

    def _load_cart_view(self):
        view = CartView(self.state, self.api)
        self.page.views.append(view)
        self.page.run_task(view.load_cart)

    def _load_orders_view(self):
        view = OrdersView(self.state, self.api)
        self.page.views.append(view)
        self.page.run_task(view.load_orders)

    def _load_dashboard_view(self):
        view = DashboardView(self.state, self.api)
        self.page.views.append(view)
        self.page.run_task(view.load_stats)

    def on_login_success(self):
        """Actions après connexion réussie."""
        username = self.state.user.user_data.get("username", "Utilisateur")
        self._show_snack_bar(f"Bienvenue {username} ! 🎉")
        self.page.go("/marketplace")
