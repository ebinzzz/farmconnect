"""adminpanel/views.py"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.models import User
from apps.products.models import Product
from apps.orders.models import Order
from .decorators import admin_required


@admin_required
def dashboard(request):
    return render(request, "admin/dashboard.html", {
        "total_users":    User.objects.count(),
        "total_farmers":  User.objects.filter(role="farmer").count(),
        "total_consumers": User.objects.filter(role="consumer").count(),
        "total_products": Product.objects.count(),
        "total_orders":   Order.objects.count(),
        "pending_orders": Order.objects.filter(status=Order.PENDING).count(),
        "recent_users":   User.objects.order_by("-date_joined")[:10],
        "recent_orders":  Order.objects.order_by("-created_at")[:10],
    })


@admin_required
def user_list(request):
    role  = request.GET.get("role", "")
    users = User.objects.all().order_by("-date_joined")
    if role:
        users = users.filter(role=role)
    return render(request, "admin/user_list.html", {"users": users, "role_filter": role})


@admin_required
def toggle_user_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.full_name} has been {status}.")
    return redirect("adminpanel:user_list")


@admin_required
def product_list(request):
    products = Product.objects.select_related("farmer", "category").order_by("-created_at")
    return render(request, "admin/product_list.html", {"products": products})


@admin_required
def order_list(request):
    orders = Order.objects.select_related("consumer").order_by("-created_at")
    return render(request, "admin/order_list.html", {"orders": orders})
