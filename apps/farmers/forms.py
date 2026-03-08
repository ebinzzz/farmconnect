from django import forms
from apps.products.models import Product, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name":        forms.TextInput(attrs={"class": "form-control"}),
        }


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        farmer = kwargs.pop("farmer", None)
        super().__init__(*args, **kwargs)
        if farmer:
            self.fields["category"].queryset = Category.objects.filter(farmer=farmer)

    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "unit", "stock", "image", "is_available"]
        widgets = {
            "name":        forms.TextInput(attrs={"class": "form-control"}),
            "category":    forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price":       forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "unit":        forms.Select(attrs={"class": "form-select"}),
            "stock":       forms.NumberInput(attrs={"class": "form-control"}),
            "image":       forms.FileInput(attrs={"class": "form-control"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
