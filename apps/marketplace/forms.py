# marketplace/forms.py
from django import forms

class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        label="Nom complet",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sekou Kerfala Bangoura'})
    )
    phone = forms.CharField(
        max_length=20,
        label="Téléphone",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+224 6 00 00 00 00'})
    )
    address_line_1 = forms.CharField(
        max_length=200,
        label="Adresse ligne 1",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pays'})
    )
    address_line_2 = forms.CharField(
        max_length=200,
        required=False,
        label="Complément d'adresse",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quartier'})
    )
    city = forms.CharField(
        max_length=100,
        label="Ville",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'})
    )
    postal_code = forms.CharField(
        max_length=20,
        label="Code postal",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '75001'})
    )
    notes = forms.CharField(
        required=False,
        label="Notes pour le producteur",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Ex: Laisser devant la porte, appeler avant livraison...'
        })
    )


# from django import forms

# class CheckoutForm(forms.Form):
#     full_name = forms.CharField(max_length=255, label="Nom complet")
#     phone = forms.CharField(max_length=20, label="Téléphone")
#     address_line_1 = forms.CharField(max_length=255, label="Adresse ligne 1")
#     address_line_2 = forms.CharField(max_length=255, required=False, label="Complément d'adresse")
#     city = forms.CharField(max_length=100, label="Ville")
#     postal_code = forms.CharField(max_length=20, label="Code postal")
#     notes = forms.CharField(widget=forms.Textarea, required=False, label="Notes pour le producteur")