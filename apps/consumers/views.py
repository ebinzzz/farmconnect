"""consumers/views.py"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.orders.models import Order


@login_required
def dashboard(request):
    orders = Order.objects.filter(consumer=request.user)
    return render(request, "consumer/dashboard.html", {
        "orders": orders[:5],
        "total_orders": orders.count(),
        "delivered": orders.filter(status=Order.DELIVERED).count(),
        "pending": orders.filter(status=Order.PENDING).count(),
    })
