from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Order, OrderItem, Cart, CartItem, Payment
from apps.products.models import Product
import razorpay


# ── Cart ──────────────────────────────────────────────────────────────────────

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


# ── Checkout & Orders ─────────────────────────────────────────────────────────

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

        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount_paise = int(total_amount * 100)
        
        # Create Razorpay Order
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1"
        })

        # Store checkout details in session instead of creating Order immediately
        request.session['checkout_data'] = {
            'delivery_address': address,
            'razorpay_order_id': razorpay_order['id'],
            'amount': float(total_amount)
        }

        context = {
            "total_amount": total_amount,
            "razorpay_order_id": razorpay_order['id'],
            "razorpay_merchant_key": settings.RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "currency": "INR",
            "consumer": request.user
        }
        return render(request, "consumer/payment.html", context)

    return render(request, "consumer/checkout.html", {"cart": cart})


@login_required
def verify_payment(request):
    if request.method == "POST":
        data = request.POST
        checkout_data = request.session.get('checkout_data')

        if not checkout_data:
            messages.error(request, "Session expired or invalid request.")
            return redirect("orders:cart")

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            }
            client.utility.verify_payment_signature(params_dict)

            with transaction.atomic():
                # Create Order
                order = Order.objects.create(
                    consumer=request.user,
                    delivery_address=checkout_data['delivery_address'],
                    total_amount=checkout_data['amount']
                )

                # Create Order Items and Deduct Stock
                cart = Cart.objects.get(consumer=request.user)
                for cart_item in cart.cart_items.select_related("product"):
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                    )
                    p = cart_item.product
                    p.stock = max(0, p.stock - cart_item.quantity)
                    p.save(update_fields=["stock"])

                # Create Payment Record
                Payment.objects.create(
                    order=order,
                    razorpay_order_id=data.get('razorpay_order_id'),
                    razorpay_payment_id=data.get('razorpay_payment_id'),
                    razorpay_signature=data.get('razorpay_signature'),
                    amount=order.total_amount,
                    status='success'
                )

                # Clear Cart & Session
                cart.cart_items.all().delete()
                del request.session['checkout_data']

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
        # Farmers see orders containing their products
        order_ids = OrderItem.objects.filter(
            product__farmer=request.user
        ).values_list("order_id", flat=True)
        orders = Order.objects.filter(pk__in=order_ids)
    else:
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

    # 1. Farmer Logic
    if request.user.is_farmer:
        valid = [Order.ACCEPTED, Order.DISPATCHED, Order.DELIVERED, Order.CANCELLED]
        if new_status in valid:
            order.status = new_status
            order.save(update_fields=["status"])
            messages.success(request, f"Order status updated to {new_status}.")
        return redirect("orders:order_detail", pk=pk)

    # 2. Delivery Agent Logic
    elif hasattr(request.user, 'agent_profile') and order.internal_agent == request.user.agent_profile:
        if new_status == Order.DELIVERED:
            order.status = Order.DELIVERED
            order.save(update_fields=["status"])
            messages.success(request, "Order marked as delivered! 🎉")
        return redirect("orders:agent_dashboard")

    # 3. Access Denied
    else:
        messages.error(request, "Access denied.")
        return redirect("products:list")


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, consumer=request.user)
    if order.status in [Order.PENDING, Order.ACCEPTED]:
        order.status = Order.CANCELLED
        order.save(update_fields=["status"])
        # Restore stock
        for item in order.items.all():
            p = item.product
            p.stock += item.quantity
            p.save(update_fields=["stock"])
        messages.success(request, "Order cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled.")
    return redirect("orders:order_detail", pk=pk)


# ── Delivery Agent Views ──────────────────────────────────────────────────────

@login_required
def agent_dashboard(request):
    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Access denied. Not a delivery agent.")
        return redirect("products:list")
    
    # Show orders assigned to this agent that are dispatched (active)
    orders = Order.objects.filter(
        internal_agent=request.user.agent_profile,
        status=Order.DISPATCHED
    ).order_by("created_at")
    
    return render(request, "delivery/dashboard.html", {"orders": orders})


@login_required
def agent_history(request):
    if not hasattr(request.user, 'agent_profile'):
        return redirect("products:list")
        
    orders = Order.objects.filter(
        internal_agent=request.user.agent_profile,
        status=Order.DELIVERED
    ).order_by("-updated_at")
    return render(request, "delivery/history.html", {"orders": orders})
