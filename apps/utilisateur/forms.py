from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import Utilisateur, ProducerProfile
from django.contrib.auth.forms import PasswordResetForm,SetPasswordForm as BaseSetPasswordForm

# #ceci est le formulaire pour éditer le profil utilisateur
# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = Utilisateur
#         fields = ['phone', 'location', 'email']
    
#     phone = forms.CharField(
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': '+33 6 XX XX XX XX'
#         }),
#         help_text="Format : +33 6 XX XX XX XX",
#         required=False
#     )
    
#     location = forms.CharField(
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Ville, Région'
#         }),
#         help_text="Ville, Région",
#         required=False
#     )
    
#     email = forms.EmailField(
#         widget=forms.EmailInput(attrs={
#             'class': 'form-control',
#         }),
#         help_text="Cet email sera public",
#     )

#ceci est le formulaire personnalisé pour le reset de mot de passe
class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajoute la classe form-control au champ email
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Votre adresse email',
            'autocomplete': 'email',
            'autofocus': True  # Optionnel : focus automatique au chargement
        })
        # Tu peux aussi customiser le label si tu veux
        self.fields['email'].label = "Adresse email"

#ceci est le formulaire personnalisé pour le reset de mot de passe (confirmation)
class CustomSetPasswordForm(BaseSetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nouveau mot de passe'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmer le mot de passe'})        


class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=Utilisateur.Role.choices,
        label="Rôle",
        widget=forms.Select(attrs={'class': 'form-control'})  # ← Style direct
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2', 'role', 'phone', 'location']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de téléphone'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emplacement (ex: coordonnées GPS)'
            }),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',    
                'placeholder': 'Mot de passe'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirmer le mot de passe'
            }),
        }

    # Option bonus : style aussi les password fields (pas dans Meta car hérités)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
        # Optionnel : ajout d'un peu de style au label du rôle
        self.fields['role'].widget.attrs.update({'class': 'form-control'})

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nom d\'utilisateur',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Mot de passe',
    }))

class UserProfileEditForm(UserChangeForm):
    password = None  # Pas d'édition password ici (utilise view dédiée si besoin)

    class Meta:
        model = Utilisateur
        fields = [ 'email', 'phone', 'location']  # Rôle éditable par admin seulement ?
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@gmail.com'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder' : '+224 000 00 00 00'}),
            'location': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder' : 'Pays, ville, quartier ?'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control form-control-textarea'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})    

class ProducerProfileEditForm(forms.ModelForm):
    class Meta:
        model = ProducerProfile
        fields = ['is_organic', 'description', 'certifications']  # Champs pour producteurs
        widgets = {
            'is_organic': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-textarea',
                'rows': 6,
                'placeholder': 'Décrivez votre exploitation, vos valeurs, vos méthodes...'}),
            'certifications': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: AOP, IGP, HVE, Label Rouge...'
            }),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control form-control-textarea'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})      