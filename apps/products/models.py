"""
products/models.py
Product listings created by Farmers
"""

from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=10, default="🌿")
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fc_categories"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ("kg",    "Kilogram"),
        ("g",     "Gram"),
        ("litre", "Litre"),
        ("dozen", "Dozen"),
        ("piece", "Piece"),
        ("bunch", "Bunch"),
        ("bag",   "Bag"),
    ]

    farmer      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name="products", limit_choices_to={"role": "farmer"})
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    unit        = models.CharField(max_length=10, choices=UNIT_CHOICES, default="kg")
    stock       = models.PositiveIntegerField(default=0)
    image       = models.ImageField(upload_to="products/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fc_products"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} by {self.farmer.full_name}"

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0
