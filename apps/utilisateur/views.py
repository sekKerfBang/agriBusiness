from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, View
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
        return reverse_lazy('marketplace:home')

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('marketplace:home')  

class UserRegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'utilisateur/register.html'
    success_url = reverse_lazy('utilisateur:login')

    def form_valid(self, form):
        response = super().form_valid(form)  

        if form.instance.role == 'ENTREPRISE':
            ProducerProfile.objects.create(user=form.instance)

        return response

class UserProfileView(LoginRequiredMixin, DetailView):
    model = Utilisateur
    template_name = 'utilisateur/profile.html'
    context_object_name = 'user_profile'

    def get_object(self, queryset=None):
        """Affiche toujours le profil de l'utilisateur connecté"""
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialisation sécurisée du producer_profile
        context['producer_profile'] = None
        context['is_producer'] = False

        if self.object.is_entreprise:
            try:
                context['producer_profile'] = ProducerProfile.objects.get(user=self.object)
                context['is_producer'] = True
            except ProducerProfile.DoesNotExist:
                # Cas où is_entreprise=True mais pas de ProducerProfile (ex: bug ou migration)
                context['is_producer'] = False
                # Optionnel : message d'avertissement
                # messages.warning(self.request, "Votre profil producteur est incomplet.")

        # Gestion de last_password_change
        context['last_password_change'] = (
            self.object.last_password_change.strftime("%d/%m/%Y à %H:%M")
            if self.object.last_password_change
            else "Non disponible"
        )

        return context

from django.shortcuts import render, redirect
from django.contrib import messages

class UserProfileEditView(LoginRequiredMixin, View):
    template_name = 'utilisateur/profile_edit.html'

    def get(self, request):
        user_form = UserProfileEditForm(instance=request.user)
        producer_form = None
        producer_profile = None

        if request.user.is_entreprise:
            # get_or_create pour éviter l'erreur si le profil n'existe pas
            producer_profile, created = ProducerProfile.objects.get_or_create(user=request.user)
            producer_form = ProducerProfileEditForm(instance=producer_profile)

        return render(request, self.template_name, {
            'user_form': user_form,
            'producer_form': producer_form,
            'producer_profile': producer_profile,
        })

    def post(self, request):
        user_form = UserProfileEditForm(request.POST, request.FILES, instance=request.user)
        producer_form = None
        producer_profile = None

        if request.user.is_entreprise:
            # On récupère ou crée le profil producteur
            producer_profile, _ = ProducerProfile.objects.get_or_create(user=request.user)
            producer_form = ProducerProfileEditForm(request.POST, request.FILES, instance=producer_profile)

        # Validation des formulaires
        forms_valid = user_form.is_valid()
        if producer_form:
            forms_valid = forms_valid and producer_form.is_valid()

        if forms_valid:
            user_form.save()
            if producer_form:
                producer_form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('utilisateur:profile')

        # En cas d'erreur, on réaffiche le formulaire avec les erreurs
        return render(request, self.template_name, {
            'user_form': user_form,
            'producer_form': producer_form,
            'producer_profile': producer_profile,
        })
# class UserProfileView(LoginRequiredMixin, DetailView):
#     model = Utilisateur
#     template_name = 'utilisateur/profile.html'
#     context_object_name = 'user_profile'

#     def get_object(self):
#         return self.request.user  # Affiche profil de l'user connecté (pas besoin pk)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.object.is_entreprise:
#             context['producer_profile'] = ProducerProfile.objects.get(user=self.object)
#         #     Fallback pour last_password_change si non set
#         if not self.object.last_password_change:
#             context['last_password_change'] = "Non disponible"
#         return context

# from django.shortcuts import render, redirect
# from django.contrib import messages
# class UserProfileEditView(LoginRequiredMixin, View):
#     template_name = 'utilisateur/profile_edit.html'
#     def get(self, request):
#         user_form = UserProfileEditForm(instance=request.user)
#         producer_form = None
#         producer_profile = None
#         if request.user.is_entreprise:
#             producer_profile = ProducerProfile.objects.get_or_create(user=request.user)[0]
#             producer_form = ProducerProfileEditForm(instance=producer_profile)
#         return render(request, self.template_name, {
#             'user_form': user_form,
#             'producer_form': producer_form,
#             'producer_profile': producer_profile
#         })

#     def post(self, request):
#         user_form = UserProfileEditForm(request.POST, request.FILES, instance=request.user)
#         producer_form = None
#         if request.user.is_entreprise:
#             producer_profile = ProducerProfile.objects.get(user=request.user)
#             producer_form = ProducerProfileEditForm(request.POST, request.FILES, instance=producer_profile)

#         if user_form.is_valid() and (not producer_form or producer_form.is_valid()):
#             user_form.save()
#             if producer_form:
#                 producer_form.save()
#             messages.success(request, 'Votre profil a été mis à jour avec succès !')
#             return redirect('utilisateur:profile')
        
#         return render(request, self.template_name, {
#             'user_form': user_form,
#             'producer_form': producer_form
#         })
     
    # def get_object(self):
    #     return self.request.user  # Édite profil connecté

    # def get_form_class(self):
    #     if self.request.user.is_entreprise:
    #         return ProducerProfileEditForm  # Forme spécifique pour producteurs
    #     return UserProfileEditForm  # Forme basique pour clients

    # def get_success_url(self):
    #     return reverse_lazy('utilisateur:profile', kwargs={'pk': self.request.user.pk})

    # def form_valid(self, form):
    #     response = super().form_valid(form)
    #     if self.request.user.is_entreprise:
    #         producer = ProducerProfile.objects.get(user=self.request.user)
    #         producer.is_organic = form.cleaned_data.get('is_organic', producer.is_organic)
    #         producer.description = form.cleaned_data.get('description', producer.description)
    #         producer.certifications = form.cleaned_data.get('certifications', producer.certifications)
    #         producer.save()  # Sauvegarde profil producteur
    #     return response

    # def get_form(self):
    #     form = super().get_form()
    #     if self.request.user.is_entreprise:
    #         producer = ProducerProfile.objects.get(user=self.request.user)
    #         form.fields['is_organic'].initial = producer.is_organic
    #         form.fields['description'].initial = producer.description
    #         form.fields['certifications'].initial = producer.certifications
    #     return form
    
    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     # Si MDP changé dans form (ex. : fields 'password', 'confirm_password')
    #     password = self.cleaned_data.get('password')
    #     if password:
    #         user.set_password(password)  # Appelle set_password (update last_password_change auto)
    #     if commit:
    #         user.save()
    #     return user
    

## NOTIFICATIONS ET EMAILS GÉRÉS DANS services/email_service.py ##
from django.views.generic import ListView
from .models import Notification
from django.contrib import messages

class NotificationsView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'utilisateur/notifications.html' 
    context_object_name = 'notifications'
    paginate_by = 20
    ordering = ['-created_at']  

    def get_queryset(self):
        """Retourne les notifications de l'utilisateur connecté"""
        return Notification.objects.filter(user=self.request.user).select_related(
            'related_order', 'related_product'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()
        return context

    def post(self, request, *args, **kwargs):
        """Gère les actions POST : marquer tout lu ou une seule lu"""
        if 'mark_all_read' in request.POST:
            updated = Notification.objects.filter(
                user=request.user, is_read=False
            ).update(is_read=True)
            if updated:
                messages.success(request, f"{updated} notification(s) marquée(s) comme lue(s).")
            else:
                messages.info(request, "Aucune nouvelle notification à marquer.")

        elif 'mark_read' in request.POST:
            notification_id = request.POST.get('notification_id')
            try:
                notif = Notification.objects.get(
                    id=notification_id, user=request.user
                )
                notif.is_read = True
                notif.save(update_fields=['is_read'])
                messages.success(request, "Notification marquée comme lue.")
            except Notification.DoesNotExist:
                messages.error(request, "Notification introuvable.")

        return redirect('utilisateur:notifications')