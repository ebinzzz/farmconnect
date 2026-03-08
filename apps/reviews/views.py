"""reviews/views.py"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from apps.products.models import Product


@login_required
def add_review(request, product_id):
    if not request.user.is_consumer:
        messages.error(request, "Only consumers can leave reviews.")
        return redirect("products:detail", pk=product_id)

    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        rating  = request.POST.get("rating")
        comment = request.POST.get("comment", "")
        Review.objects.update_or_create(
            consumer=request.user,
            product=product,
            defaults={"rating": rating, "comment": comment},
        )
        messages.success(request, "Your review has been submitted. Thanks!")
    return redirect("products:detail", pk=product_id)
