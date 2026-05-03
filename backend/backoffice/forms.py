from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, SetPasswordForm

from products.models import InvestmentProduct

User = get_user_model()


class BOLoginForm(AuthenticationForm):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class InvestmentProductForm(forms.ModelForm):
    class Meta:
        model = InvestmentProduct
        fields = [
            "name",
            "image_url",
            "image",
            "description",
            "min_investment_cdf",
            "estimated_gain_cdf",
            "duration_days",
            "note",
            "performance_factor",
            "is_active",
        ]
        labels = {
            "name": "Nom du produit",
            "image_url": "Lien image (Internet) — recommandé",
            "image": "Upload image (optionnel)",
            "description": "Description",
            "min_investment_cdf": "Investissement minimum (FC)",
            "estimated_gain_cdf": "Gain estimé (FC) — NON GARANTI",
            "duration_days": "Durée estimée (jours)",
            "note": "Note (Fiable / Pas vraiment / Populaire)",
            "performance_factor": "Indice de performance (variable)",
            "is_active": "Actif (visible sur le site)",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "image_url": forms.URLInput(attrs={"placeholder": "https://exemple.com/image.jpg"}),
        }


class AdminUserCreateForm(UserCreationForm):
    is_staff = forms.BooleanField(label="Administrateur (accès gestion)", required=False)
    is_active = forms.BooleanField(label="Actif", required=False, initial=True)

    class Meta:
        model = User
        fields = ("username", "is_staff", "is_active", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data.get("is_staff", False)
        user.is_active = self.cleaned_data.get("is_active", True)
        if commit:
            user.save()
        return user


class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "is_staff", "is_active")
        labels = {
            "username": "Nom d'utilisateur",
            "is_staff": "Administrateur (accès gestion)",
            "is_active": "Actif",
        }


class AdminUserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="Nouveau mot de passe", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirmer mot de passe", widget=forms.PasswordInput)