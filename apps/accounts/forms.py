from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "role"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email":     forms.EmailInput(attrs={"class": "form-control"}),
            "phone":     forms.TextInput(attrs={"class": "form-control"}),
            "role":      forms.Select(attrs={"class": "form-select"},
                                      choices=[("farmer", "Farmer 🧑‍🌾"), ("consumer", "Consumer 🛒")]),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"class": "form-control", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
