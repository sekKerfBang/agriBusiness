from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import UserRegisterForm, UserProfileEditForm, ProducerProfileEditForm, LoginForm
from .models import Utilisateur, ProducerProfile
from django.http import HttpResponseRedirect, HttpResponse

class UserLoginView(LoginView):
    template_name = 'utilisateur/login.html'  # Template global
    form_class = LoginForm  # Utilise le formulaire par défaut de Django
    
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Logique de connexion standard
        response = super().form_valid(form)
        if self.request.htmx:
            # Pour HTMX, utiliser l'en-tête HX-Redirect pour une navigation pleine page
            success_url = self.get_success_url()
            resp = HttpResponse(status=200)
            resp['HX-Redirect'] = success_url
            return resp
        return response

    def get_success_url(self):
        # Redirige toujours vers marketplace:home après login
        return reverse_lazy('dashboard:index')

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('marketplace:home')  # Redirige après logout

class UserRegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'utilisateur/register.html'
    success_url = reverse_lazy('utilisateur:login')  # Redirige vers login après inscription

    def form_valid(self, form):
        response = super().form_valid(form)
        if form.instance.role == 'ENTREPRISE':
            ProducerProfile.objects.create(user=form.instance)  # Crée profil auto pour producteurs
        return response

class UserProfileView(LoginRequiredMixin, DetailView):
    model = Utilisateur
    template_name = 'utilisateur/profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return self.request.user  # Affiche profil de l'user connecté (pas besoin pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.is_entreprise:
            context['producer_profile'] = ProducerProfile.objects.get(user=self.object)
        #     Fallback pour last_password_change si non set
        if not self.object.last_password_change:
            context['last_password_change'] = "Non disponible"
        return context

class UserProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = 'utilisateur/profile_edit.html'

     
    def get_object(self):
        return self.request.user  # Édite profil connecté

    def get_form_class(self):
        if self.request.user.is_entreprise:
            return ProducerProfileEditForm  # Forme spécifique pour producteurs
        return UserProfileEditForm  # Forme basique pour clients

    def get_success_url(self):
        return reverse_lazy('utilisateur:profile', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_entreprise:
            producer = ProducerProfile.objects.get(user=self.request.user)
            producer.is_organic = form.cleaned_data.get('is_organic', producer.is_organic)
            producer.description = form.cleaned_data.get('description', producer.description)
            producer.certifications = form.cleaned_data.get('certifications', producer.certifications)
            producer.save()  # Sauvegarde profil producteur
        return response

    def get_form(self):
        form = super().get_form()
        if self.request.user.is_entreprise:
            producer = ProducerProfile.objects.get(user=self.request.user)
            form.fields['is_organic'].initial = producer.is_organic
            form.fields['description'].initial = producer.description
            form.fields['certifications'].initial = producer.certifications
        return form
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Si MDP changé dans form (ex. : fields 'password', 'confirm_password')
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)  # Appelle set_password (update last_password_change auto)
        if commit:
            user.save()
        return user