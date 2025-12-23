import flet as ft

class AuthView(ft.View):
    def __init__(self, state, api, on_success):
        super().__init__(route="/auth")
        self.state = state
        self.api = api
        self.on_success = on_success
        
        self.username = ft.TextField(label="Nom d'utilisateur", width=300, bgcolor=ft.Colors.WHITE10)
        self.password = ft.TextField(label="Mot de passe", password=True, width=300, bgcolor=ft.Colors.WHITE10)
        self.error_text = ft.Text(color=ft.Colors.RED, visible=False)
        self.login_btn = ft.ElevatedButton(
            "Connexion", 
            on_click=self.handle_login,
            width=300,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE
        )
        
        content = ft.Column([
            ft.Text("Bienvenue sur AgriMarket", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            self.username,
            self.password,
            self.error_text,
            self.login_btn,
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.controls = [
            ft.AppBar(title=ft.Text("Connexion"), bgcolor=ft.Colors.GREEN),
            ft.Container(content=content, alignment=ft.alignment.center, expand=True, padding=20)
        ]
    
    async def handle_login(self, e):
        if not self.username.value or not self.password.value:
            self.error_text.value = "Veuillez remplir tous les champs"
            self.error_text.visible = True
        else:
            result = await self.api.login(self.username.value, self.password.value)
            if result:
                self.state.user.is_authenticated = True
                self.state.user.token = result["access"]
                self.state.user.user_data = result.get("user", {})
                self.state.user.role = self.state.user.user_data.get("role")
                await self.state.save_to_storage()
                self.on_success()
            else:
                self.error_text.value = "Identifiants invalides"
                self.error_text.visible = True
        # self.update()



# import flet as ft

# class AuthView(ft.View):
#     def __init__(self, state, api, on_success):
#         super().__init__(route="/auth")
#         self.state = state
#         self.api = api
#         self.on_success = on_success
        
#         self.username = ft.TextField(label="Nom d'utilisateur", width=300)
#         self.password = ft.TextField(label="Mot de passe", password=True, width=300)
#         self.error_text = ft.Text(color=ft.colors.RED, visible=False)
#         self.login_btn = ft.ElevatedButton(
#             "Connexion", 
#             on_click=self.handle_login,
#             width=300,
#             bgcolor=ft.colors.GREEN,
#             color=ft.colors.WHITE
#         )
        
#         self.controls = [
#             ft.AppBar(title=ft.Text("Connexion"), bgcolor=ft.colors.GREEN),
#             ft.Container(
#                 content=ft.Column([
#                     ft.Text("Bienvenue sur AgriMarket", size=24, weight=ft.FontWeight.BOLD),
#                     self.username,
#                     self.password,
#                     self.error_text,
#                     self.login_btn,
#                 ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
#                 alignment=ft.alignment.center,
#                 expand=True,
#             )
#         ]
    
#     async def handle_login(self, e):
#         """Gère la connexion"""
#         self.error_text.visible = False
        
#         if not self.username.value or not self.password.value:
#             self.error_text.value = "Veuillez remplir tous les champs"
#             self.error_text.visible = True
#             self.update()
#             return
        
#         result = await self.api.login(self.username.value, self.password.value)
        
#         if result:
#             self.state.user.is_authenticated = True
#             self.state.user.token = result["access"]
#             self.state.user.user_data = result.get("user", {})
#             self.state.user.role = self.state.user.user_data.get("role")
            
#             # Sauvegarder le token
#             self.page.client_storage.set("auth_token", result["access"])
            
#             self.on_success()
#         else:
#             self.error_text.value = "Identifiants invalides"
#             self.error_text.visible = True
#             self.update()