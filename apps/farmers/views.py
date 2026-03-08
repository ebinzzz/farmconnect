"""farmers/views.py – Farmer dashboard + product management"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Sum, Count
from django.forms import modelform_factory
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem, DeliveryAgent
from .forms import ProductForm
from .decorators import farmer_required


@login_required
def dashboard(request):
    # Dispatch based on role to prevent redirect loops
    if getattr(request.user, 'role', None) == 'agent':
        return redirect("orders:agent_dashboard")
    if not getattr(request.user, 'is_farmer', False):
        return redirect("products:list")

    farmer   = request.user
    products = Product.objects.filter(farmer=farmer)
    order_ids = OrderItem.objects.filter(product__farmer=farmer).values_list("order_id", flat=True)
    orders   = Order.objects.filter(pk__in=order_ids)
    total_sales = orders.filter(status=Order.DELIVERED).aggregate(
        total=Sum("total_amount"))["total"] or 0
    pending_count = orders.filter(status=Order.PENDING).count()

    return render(request, "farmer/dashboard.html", {
        "products": products,
        "orders": orders[:5],
        "total_sales": total_sales,
        "pending_count": pending_count,
        "product_count": products.count(),
    })


@farmer_required
def product_add(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.farmer = request.user
        product.save()
        messages.success(request, f"'{product.name}' listed successfully! 🌾")
        return redirect("farmers:dashboard")
    return render(request, "farmer/product_form.html", {"form": form, "action": "Add"})


@farmer_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, farmer=request.user)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("farmers:dashboard")
    return render(request, "farmer/product_form.html", {"form": form, "action": "Edit"})


@farmer_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, farmer=request.user)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product removed.")
    return redirect("farmers:dashboard")


@farmer_required
def order_list(request):
    order_ids = OrderItem.objects.filter(product__farmer=request.user).values_list("order_id", flat=True)
    orders = Order.objects.filter(pk__in=order_ids).order_by("-created_at")

    # Filtering
    status = request.GET.get("status")
    date_param = request.GET.get("date")
    delivery_date_param = request.GET.get("delivery_date")

    if status:
        orders = orders.filter(status=status)
    if date_param:
        orders = orders.filter(created_at__date=date_param)
    if delivery_date_param:
        orders = orders.filter(expected_delivery_date=delivery_date_param)

    return render(request, "farmer/order_list.html", {
        "orders": orders,
        "status_choices": Order.STATUS_CHOICES
    })


@farmer_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Ensure the farmer has items in this order before showing it
    if not OrderItem.objects.filter(order=order, product__farmer=request.user).exists():
        messages.error(request, "You are not authorized to view this order.")
        return redirect("farmers:order_list")

    agents = DeliveryAgent.objects.filter(farmer=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status:
            order.status = new_status
            
            # Capture delivery details if dispatched
            if new_status == Order.DISPATCHED:
                order.delivery_type = request.POST.get("delivery_type")
                if order.delivery_type == "internal":
                    agent_id = request.POST.get("internal_agent")
                    if agent_id:
                        order.internal_agent_id = agent_id
                elif order.delivery_type == "external":
                    order.external_service_name = request.POST.get("external_service_name")
                    order.tracking_link = request.POST.get("tracking_link")
                    order.tracking_code = request.POST.get("tracking_code")
                    order.expected_delivery_date = request.POST.get("expected_delivery_date") or None

            order.save()
            messages.success(request, f"Order status updated to {order.get_status_display()}.")
            return redirect("farmers:order_detail", pk=pk)

    return render(request, "farmer/order_detail.html", {
        "order": order,
        "status_choices": Order._meta.get_field('status').choices,
        "agents": agents
    })


# ── Agent Management ──────────────────────────────────────────────────────────

@farmer_required
def agent_list(request):
    agents = DeliveryAgent.objects.filter(farmer=request.user)
    return render(request, "farmer/agent_list.html", {"agents": agents})


@farmer_required
def agent_add(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            user = User.objects.create(
                email=email,
                password=make_password(password),
                full_name=name,
                role='agent',
                is_active=True
            )
            DeliveryAgent.objects.create(
                farmer=request.user, user=user, name=name, phone=phone
            )
            messages.success(request, "Delivery agent created with login access.")
            return redirect("farmers:agent_list")
    return render(request, "farmer/agent_form.html", {"action": "Add"})


@farmer_required
def agent_edit(request, pk):
    agent = get_object_or_404(DeliveryAgent, pk=pk, farmer=request.user)
    AgentForm = modelform_factory(DeliveryAgent, fields=("name", "phone"))
    form = AgentForm(request.POST or None, instance=agent)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Agent updated.")
        return redirect("farmers:agent_list")
    return render(request, "farmer/agent_form.html", {"form": form, "action": "Edit"})


@farmer_required
def agent_delete(request, pk):
    agent = get_object_or_404(DeliveryAgent, pk=pk, farmer=request.user)
    if request.method == "POST":
        agent.delete()
        messages.success(request, "Agent removed.")
    return redirect("farmers:agent_list")


@farmer_required
def agent_orders(request, pk):
    agent = get_object_or_404(DeliveryAgent, pk=pk, farmer=request.user)
    orders = Order.objects.filter(internal_agent=agent).order_by("-created_at")

    # Filtering
    status = request.GET.get("status")
    date_param = request.GET.get("date")

    if status:
        orders = orders.filter(status=status)
    if date_param:
        orders = orders.filter(created_at__date=date_param)

    return render(request, "farmer/agent_orders.html", {
        "agent": agent,
        "orders": orders,
        "status_choices": Order.STATUS_CHOICES
    })
