from django import forms
from apps.products.models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'stock', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder':'Description', 'class':'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Prix', 'class':'form-control'}),
            'stock': forms.NumberInput(attrs={'min': '0', 'placeholder': 'Stock ', 'class':'form-control'}),
            'category' : forms.Select(attrs={
                'class':'form-control',
                'placeholder': 'Category',
            }),
            'name': forms.TextInput(attrs={
                'class':'form-control',
                'placeholder': 'ex: nom fruit, legume, produit laitier'
            })
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Le prix ne peut pas être négatif.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock < 0:
            raise forms.ValidationError("Le stock ne peut pas être négatif.")
        return stock