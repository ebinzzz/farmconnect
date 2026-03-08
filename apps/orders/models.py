"""
orders/models.py
Order lifecycle: PENDING → ACCEPTED → DISPATCHED → DELIVERED | CANCELLED
"""

from django.db import models
from django.conf import settings
from apps.products.models import Product


class DeliveryAgent(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agents")
    user   = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile", null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Order(models.Model):
    PENDING    = "pending"
    ACCEPTED   = "accepted"
    PACKED     = "packed"
    DISPATCHED = "dispatched"
    DELIVERED  = "delivered"
    CANCELLED  = "cancelled"

    STATUS_CHOICES = [
        (PENDING,    "Pending"),
        (ACCEPTED,   "Accepted"),
        (PACKED,     "Packed"),
        (DISPATCHED, "Dispatched"),
        (DELIVERED,  "Delivered"),
        (CANCELLED,  "Cancelled"),
    ]

    consumer        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        related_name="orders", limit_choices_to={"role": "consumer"})
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING)
    delivery_address = models.TextField()
    total_amount    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    # Delivery Details
    delivery_type = models.CharField(max_length=20, blank=True, null=True) # internal/external
    internal_agent = models.ForeignKey(DeliveryAgent, on_delete=models.SET_NULL, null=True, blank=True)
    external_service_name = models.CharField(max_length=100, blank=True)
    tracking_link = models.URLField(blank=True)
    tracking_code = models.CharField(max_length=100, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "fc_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} – {self.consumer.full_name} ({self.status})"

    def calculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total_amount"])


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product  = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    price    = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot at time of order

    class Meta:
        db_table = "fc_order_items"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


class Cart(models.Model):
    consumer   = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                      related_name="cart", limit_choices_to={"role": "consumer"})
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fc_carts"

    @property
    def total(self):
        return sum(item.subtotal for item in self.cart_items.all())


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "fc_cart_items"
        unique_together = ("cart", "product")

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fc_payments"

    def __str__(self):
        return f"Payment for Order #{self.order.id}"
