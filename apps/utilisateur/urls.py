from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = 'utilisateur'  # Namespace pour reverses (ex: 'utilisateur:login')

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),  # Sans pk, utilise request.user
    path('profile/edit/', views.UserProfileEditView.as_view(), name='profile_edit'),  # Sans pk

     # Nouvelle : Password reset routes (built-in)
    path('password/reset/', auth_views.PasswordResetView.as_view(
        template_name='utilisateur/password_reset_form.html',  # Template global
        email_template_name='utilisateur/password_reset_email.html',  # Mail text
        form_class=CustomPasswordResetForm, # ceci est le formulaire utilisé
        success_url=reverse_lazy('password_reset_done'), # ceci est la vue à afficher après envoi
        subject_template_name='utilisateur/password_reset_subject.txt'  # Sujet mail
    ), name='password_reset'),
    
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='utilisateur/password_reset_done.html' # ceci est le template affiché après envoi
    ), name='password_reset_done'),
    
    path('password/reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='utilisateur/password_reset_confirm.html', # ceci est le template pour réinitialiser le mdp
        form_class=CustomSetPasswordForm,  # ceci est le formulaire utilisé pour réinitialiser le mdp
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='utilisateur/password_reset_complete.html'
    ), name='password_reset_complete'),
]