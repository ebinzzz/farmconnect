"""reviews/models.py"""
from django.db import models
from django.conf import settings
from apps.products.models import Product


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    consumer   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="reviews", limit_choices_to={"role": "consumer"})
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating     = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fc_reviews"
        unique_together = ("consumer", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.consumer.full_name} → {self.product.name} ({self.rating}★)"
