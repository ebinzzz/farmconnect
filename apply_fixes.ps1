# ============================================================
# FarmConnect - Apply all role-based access fixes
# Run from D:\farmconnect_win\
# Usage:  .\apply_fixes.ps1
# ============================================================

Write-Host "Applying FarmConnect fixes..." -ForegroundColor Cyan

# ── 1. accounts/models.py ─────────────────────────────────────────────────────
Set-Content -Path "apps\accounts\models.py" -Value @'
"""
accounts/models.py
Custom User model with role-based access: FARMER | CONSUMER | ADMIN | AGENT
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.ADMIN)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    FARMER   = "farmer"
    CONSUMER = "consumer"
    ADMIN    = "admin"
    AGENT    = "agent"
    ROLE_CHOICES = [
        (FARMER,   "Farmer"),
        (CONSUMER, "Consumer"),
        (ADMIN,    "Admin"),
        (AGENT,    "Delivery Agent"),
    ]

    email       = models.EmailField(unique=True)
    full_name   = models.CharField(max_length=150)
    role        = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CONSUMER)
    phone       = models.CharField(max_length=15, blank=True)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    avatar      = models.ImageField(upload_to="avatars/", blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table     = "fc_users"
        verbose_name = "User"

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def is_farmer(self):
        return self.role == self.FARMER

    @property
    def is_consumer(self):
        return self.role == self.CONSUMER

    @property
    def is_admin_user(self):
        return self.role == self.ADMIN

    @property
    def is_agent(self):
        return self.role == self.AGENT
'@
Write-Host "[1/6] accounts/models.py" -ForegroundColor Green

# ── 2. accounts/dashboard_views.py ───────────────────────────────────────────
Set-Content -Path "apps\accounts\dashboard_views.py" -Value @'
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_home(request):
    user = request.user
    if user.is_farmer:
        return redirect("farmers:dashboard")
    elif user.is_consumer:
        return redirect("consumers:dashboard")
    elif user.is_agent:
        return redirect("orders:agent_dashboard")
    elif user.is_admin_user or user.is_staff:
        return redirect("adminpanel:dashboard")
    return redirect("accounts:login")
'@
Write-Host "[2/6] accounts/dashboard_views.py" -ForegroundColor Green

# ── 3. accounts/migrations/0002_add_agent_role.py ────────────────────────────
Set-Content -Path "apps\accounts\migrations\0002_add_agent_role.py" -Value @'
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("farmer",   "Farmer"),
                    ("consumer", "Consumer"),
                    ("admin",    "Admin"),
                    ("agent",    "Delivery Agent"),
                ],
                default="consumer",
                max_length=10,
            ),
        ),
    ]
'@
Write-Host "[3/6] accounts/migrations/0002_add_agent_role.py" -ForegroundColor Green

# ── 4. farmers/decorators.py ─────────────────────────────────────────────────
Set-Content -Path "apps\farmers\decorators.py" -Value @'
# farmers/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def farmer_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not request.user.is_farmer:
            messages.error(request, "Access restricted to farmers only.")
            return redirect("products:list")
        return view_func(request, *args, **kwargs)
    return _wrapped
'@
Write-Host "[4/6] farmers/decorators.py" -ForegroundColor Green

# ── 5. orders/views.py ───────────────────────────────────────────────────────
Set-Content -Path "apps\orders\views.py" -Value @'
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from .models import Order, OrderItem, Cart, CartItem, Payment
from apps.products.models import Product
import razorpay


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(consumer=request.user)
    return render(request, "consumer/cart.html", {"cart": cart})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)
    cart, _ = Cart.objects.get_or_create(consumer=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"'{product.name}' added to cart!")
    return redirect(request.META.get("HTTP_REFERER", "products:list"))


@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__consumer=request.user)
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity"))
            if quantity > 0:
                item.quantity = quantity
                item.save()
                messages.success(request, "Cart updated.")
            else:
                item.delete()
                messages.info(request, "Item removed from cart.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
    return redirect("orders:cart")


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__consumer=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect("orders:cart")


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, consumer=request.user)
    if not cart.cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("orders:cart")

    if request.method == "POST":
        address = request.POST.get("delivery_address", "").strip()
        if not address:
            messages.error(request, "Please provide a delivery address.")
            return render(request, "consumer/checkout.html", {"cart": cart})

        total_amount = cart.total
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_paise = int(total_amount * 100)
        razorpay_order = client.order.create({"amount": amount_paise, "currency": "INR", "payment_capture": "1"})

        request.session["checkout_data"] = {
            "delivery_address": address,
            "razorpay_order_id": razorpay_order["id"],
            "amount": float(total_amount),
        }
        return render(request, "consumer/payment.html", {
            "total_amount": total_amount,
            "razorpay_order_id": razorpay_order["id"],
            "razorpay_merchant_key": settings.RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "currency": "INR",
            "consumer": request.user,
        })

    return render(request, "consumer/checkout.html", {"cart": cart})


@login_required
def verify_payment(request):
    if request.method == "POST":
        data = request.POST
        checkout_data = request.session.get("checkout_data")
        if not checkout_data:
            messages.error(request, "Session expired or invalid request.")
            return redirect("orders:cart")
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                "razorpay_order_id":   data.get("razorpay_order_id"),
                "razorpay_payment_id": data.get("razorpay_payment_id"),
                "razorpay_signature":  data.get("razorpay_signature"),
            })
            with transaction.atomic():
                order = Order.objects.create(
                    consumer=request.user,
                    delivery_address=checkout_data["delivery_address"],
                    total_amount=checkout_data["amount"],
                )
                cart = Cart.objects.get(consumer=request.user)
                for cart_item in cart.cart_items.select_related("product"):
                    OrderItem.objects.create(
                        order=order, product=cart_item.product,
                        quantity=cart_item.quantity, price=cart_item.product.price,
                    )
                    p = cart_item.product
                    p.stock = max(0, p.stock - cart_item.quantity)
                    p.save(update_fields=["stock"])
                Payment.objects.create(
                    order=order,
                    razorpay_order_id=data.get("razorpay_order_id"),
                    razorpay_payment_id=data.get("razorpay_payment_id"),
                    razorpay_signature=data.get("razorpay_signature"),
                    amount=order.total_amount,
                    status="success",
                )
                cart.cart_items.all().delete()
                del request.session["checkout_data"]
            messages.success(request, f"Payment successful! Order #{order.pk} placed.")
            return redirect("orders:order_detail", pk=order.pk)
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed.")
            return redirect("orders:cart")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("orders:cart")
    return redirect("orders:cart")


@login_required
def order_list(request):
    if request.user.is_farmer:
        return redirect("farmers:order_list")
    orders = Order.objects.filter(consumer=request.user)
    return render(request, "consumer/order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    if request.user.is_farmer:
        order_ids = OrderItem.objects.filter(product__farmer=request.user).values_list("order_id", flat=True)
        order = get_object_or_404(Order, pk=pk, id__in=order_ids)
    else:
        order = get_object_or_404(Order, pk=pk, consumer=request.user)
    return render(request, "consumer/order_detail.html", {"order": order})


@login_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get("status")

    if request.user.is_farmer:
        valid = [Order.ACCEPTED, Order.PACKED, Order.DISPATCHED, Order.DELIVERED, Order.CANCELLED]
        if new_status in valid:
            order.status = new_status
            order.save(update_fields=["status"])
            messages.success(request, f"Order status updated to {new_status}.")
        return redirect("farmers:order_detail", pk=pk)

    elif request.user.is_agent and hasattr(request.user, "agent_profile") and order.internal_agent == request.user.agent_profile:
        if new_status == Order.DELIVERED:
            order.status = Order.DELIVERED
            order.save(update_fields=["status"])
            messages.success(request, "Order marked as delivered!")
        return redirect("orders:agent_dashboard")

    else:
        messages.error(request, "Access denied.")
        return redirect("products:list")


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, consumer=request.user)
    if order.status in [Order.PENDING, Order.ACCEPTED]:
        order.status = Order.CANCELLED
        order.save(update_fields=["status"])
        for item in order.items.all():
            p = item.product
            p.stock += item.quantity
            p.save(update_fields=["stock"])
        messages.success(request, "Order cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled.")
    return redirect("orders:order_detail", pk=pk)


@login_required
def agent_dashboard(request):
    if not request.user.is_agent or not hasattr(request.user, "agent_profile"):
        messages.error(request, "Access denied. Not a delivery agent.")
        return redirect("products:list")
    orders = Order.objects.filter(
        internal_agent=request.user.agent_profile,
        status=Order.DISPATCHED,
    ).order_by("created_at")
    return render(request, "delivery/dashboard.html", {"orders": orders})


@login_required
def agent_history(request):
    if not request.user.is_agent or not hasattr(request.user, "agent_profile"):
        return redirect("products:list")
    orders = Order.objects.filter(
        internal_agent=request.user.agent_profile,
        status=Order.DELIVERED,
    ).order_by("-updated_at")
    return render(request, "delivery/history.html", {"orders": orders})
'@
Write-Host "[5/6] orders/views.py" -ForegroundColor Green

# ── 6. templates/farmer/order_detail.html ────────────────────────────────────
Set-Content -Path "templates\farmer\order_detail.html" -Value @'
{% extends "base.html" %}
{% block title %}Order #{{ order.pk }} - Farmer Panel{% endblock %}
{% block content %}
<div class="container-fluid">
  <div class="row">
    <div class="col-12 d-md-none p-3">
      <button class="btn btn-primary w-100" type="button" data-bs-toggle="offcanvas" data-bs-target="#mainSidebar">
        <i class="bi bi-list"></i> Menu
      </button>
    </div>
    <div class="col-md-2 sidebar d-none d-md-block">
      <div class="px-3 mb-4"><p class="text-muted small fw-semibold text-uppercase">Farmer Panel</p></div>
      <nav class="nav flex-column">
        <a class="nav-link" href="{% url "farmers:dashboard" %}"><i class="bi bi-speedometer2"></i> Dashboard</a>
        <a class="nav-link" href="{% url "farmers:product_add" %}"><i class="bi bi-plus-circle"></i> Add Product</a>
        <a class="nav-link active" href="{% url "farmers:order_list" %}"><i class="bi bi-bag"></i> Orders</a>
        <a class="nav-link" href="{% url "farmers:agent_list" %}"><i class="bi bi-truck"></i> Delivery Agents</a>
        <a class="nav-link" href="{% url "products:list" %}"><i class="bi bi-shop"></i> Marketplace</a>
      </nav>
    </div>
    <div class="offcanvas offcanvas-start" tabindex="-1" id="mainSidebar">
      <div class="offcanvas-header">
        <h5 class="offcanvas-title">Farmer Panel</h5>
        <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
      </div>
      <div class="offcanvas-body">
        <nav class="nav flex-column">
          <a class="nav-link" href="{% url "farmers:dashboard" %}"><i class="bi bi-speedometer2"></i> Dashboard</a>
          <a class="nav-link" href="{% url "farmers:product_add" %}"><i class="bi bi-plus-circle"></i> Add Product</a>
          <a class="nav-link active" href="{% url "farmers:order_list" %}"><i class="bi bi-bag"></i> Orders</a>
          <a class="nav-link" href="{% url "farmers:agent_list" %}"><i class="bi bi-truck"></i> Delivery Agents</a>
          <a class="nav-link" href="{% url "products:list" %}"><i class="bi bi-shop"></i> Marketplace</a>
        </nav>
      </div>
    </div>
    <div class="col-md-10 p-4">
      <div class="mb-4">
        <a href="{% url "farmers:order_list" %}" class="text-decoration-none text-muted"><i class="bi bi-arrow-left"></i> Back to Orders</a>
      </div>
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="page-title mb-0">Order #{{ order.pk }}</h4>
        <span class="badge rounded-pill fs-6 {% if order.status == "delivered" %}bg-success{% elif order.status == "pending" %}bg-warning text-dark{% elif order.status == "packed" %}bg-secondary{% elif order.status == "dispatched" %}bg-info text-dark{% elif order.status == "cancelled" %}bg-danger{% else %}bg-primary{% endif %}">
          {{ order.get_status_display }}
        </span>
      </div>
      <div class="row">
        <div class="col-md-8">
          <div class="card mb-4">
            <div class="card-header bg-light fw-bold">Order Items</div>
            <div class="card-body p-0">
              <table class="table table-hover mb-0">
                <thead><tr><th>Product</th><th class="text-center">Qty</th><th class="text-end">Price</th><th class="text-end">Subtotal</th></tr></thead>
                <tbody>
                  {% for item in order.items.all %}
                  <tr>
                    <td>{{ item.product.name }}</td>
                    <td class="text-center">{{ item.quantity }}</td>
                    <td class="text-end">Rs.{{ item.price }}</td>
                    <td class="text-end">Rs.{{ item.subtotal }}</td>
                  </tr>
                  {% endfor %}
                </tbody>
                <tfoot class="table-light">
                  <tr><td colspan="3" class="text-end fw-bold">Grand Total:</td><td class="text-end fw-bold">Rs.{{ order.total_amount }}</td></tr>
                </tfoot>
              </table>
            </div>
          </div>
          <div class="card mb-4">
            <div class="card-header bg-light fw-bold">Delivery Address</div>
            <div class="card-body">
              <p class="mb-0 text-muted">{{ order.delivery_address }}</p>
              {% if order.notes %}<hr/><p class="mb-0 text-muted"><strong>Notes:</strong> {{ order.notes }}</p>{% endif %}
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card mb-4">
            <div class="card-header bg-light fw-bold">Update Status</div>
            <div class="card-body">
              <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                  <label class="form-label">Status</label>
                  <select name="status" id="statusSelect" class="form-select" onchange="toggleDeliveryFields()">
                    {% for value, label in status_choices %}
                    <option value="{{ value }}" {% if order.status == value %}selected{% endif %}>{{ label }}</option>
                    {% endfor %}
                  </select>
                </div>
                <div id="deliveryFields" style="display:none;" class="border-top pt-3 mt-2">
                  <h6 class="small fw-bold mb-2">Delivery Information</h6>
                  <div class="mb-3">
                    <label class="form-label small">Delivery Type</label>
                    <select name="delivery_type" id="deliveryType" class="form-select form-select-sm" onchange="toggleAgentFields()">
                      <option value="">Select Type...</option>
                      <option value="internal">Internal Agent</option>
                      <option value="external">External Courier</option>
                    </select>
                  </div>
                  <div id="internalFields" style="display:none;">
                    <label class="form-label small">Select Agent</label>
                    <select name="internal_agent" class="form-select form-select-sm mb-2">
                      <option value="">Choose Agent...</option>
                      {% for agent in agents %}
                      <option value="{{ agent.pk }}">{{ agent.name }} ({{ agent.phone }})</option>
                      {% endfor %}
                    </select>
                    <div class="form-text"><a href="{% url "farmers:agent_add" %}" class="small">+ Add New Agent</a></div>
                  </div>
                  <div id="externalFields" style="display:none;">
                    <input type="text" name="external_service_name" class="form-control form-control-sm mb-2" placeholder="Service Name (e.g. FedEx)">
                    <input type="text" name="tracking_code" class="form-control form-control-sm mb-2" placeholder="Tracking Code">
                    <input type="url" name="tracking_link" class="form-control form-control-sm mb-2" placeholder="Tracking Link">
                    <input type="date" name="expected_delivery_date" class="form-control form-control-sm mb-2">
                  </div>
                </div>
                <button type="submit" class="btn btn-primary w-100 mt-2">Update Status</button>
              </form>
            </div>
          </div>
          <div class="card mb-4">
            <div class="card-header bg-light fw-bold">Customer Details</div>
            <div class="card-body">
              <p class="mb-1"><strong>Name:</strong> {{ order.consumer.full_name }}</p>
              <p class="mb-1"><strong>Email:</strong> {{ order.consumer.email }}</p>
              {% if order.consumer.phone %}<p class="mb-1"><strong>Phone:</strong> {{ order.consumer.phone }}</p>{% endif %}
              <p class="mb-0"><strong>Date:</strong> {{ order.created_at|date:"F d, Y H:i" }}</p>
            </div>
          </div>
          {% if order.delivery_type %}
          <div class="card mb-4">
            <div class="card-header bg-light fw-bold">Dispatch Details</div>
            <div class="card-body">
              {% if order.delivery_type == "internal" %}
                <p class="mb-1"><strong>Agent:</strong> {{ order.internal_agent.name }}</p>
                <p class="mb-0"><strong>Phone:</strong> {{ order.internal_agent.phone }}</p>
              {% else %}
                <p class="mb-1"><strong>Service:</strong> {{ order.external_service_name }}</p>
                <p class="mb-1"><strong>Tracking:</strong> {{ order.tracking_code }}</p>
                {% if order.tracking_link %}<p class="mb-0"><a href="{{ order.tracking_link }}" target="_blank">Track Package</a></p>{% endif %}
              {% endif %}
            </div>
          </div>
          {% endif %}
          {% if order.payment %}
          <div class="card mb-4">
            <div class="card-header bg-light fw-bold">Payment</div>
            <div class="card-body">
              <div class="d-flex justify-content-between mb-2">
                <span>Status:</span>
                <span class="badge {% if order.payment.status == "success" %}bg-success{% else %}bg-warning text-dark{% endif %}">{{ order.payment.status|title }}</span>
              </div>
              <p class="mb-1"><strong>ID:</strong> {{ order.payment.razorpay_payment_id|default:"-" }}</p>
              <p class="mb-0"><strong>Amount:</strong> Rs.{{ order.payment.amount }}</p>
            </div>
          </div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>
<script>
function toggleDeliveryFields() {
  document.getElementById("deliveryFields").style.display =
    document.getElementById("statusSelect").value === "dispatched" ? "block" : "none";
}
function toggleAgentFields() {
  const t = document.getElementById("deliveryType").value;
  document.getElementById("internalFields").style.display = t === "internal" ? "block" : "none";
  document.getElementById("externalFields").style.display = t === "external" ? "block" : "none";
}
document.addEventListener("DOMContentLoaded", toggleDeliveryFields);
</script>
{% endblock %}
'@
Write-Host "[6/6] templates/farmer/order_detail.html" -ForegroundColor Green

Write-Host ""
Write-Host "All files updated! Now running migration..." -ForegroundColor Cyan
python manage.py migrate
Write-Host ""
Write-Host "Done! Start server with: python manage.py runserver" -ForegroundColor Yellow
