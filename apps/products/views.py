from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Product, Category


def product_list(request):
    products   = Product.objects.filter(is_available=True, stock__gt=0)
    categories = Category.objects.all()
    query      = request.GET.get("q", "")
    category   = request.GET.get("category", "")
    min_price  = request.GET.get("min_price", "")
    max_price  = request.GET.get("max_price", "")

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category:
        products = products.filter(category__slug=category)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    return render(request, "consumer/product_list.html", {
        "products": products,
        "categories": categories,
        "query": query,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_available=True)
    reviews = product.reviews.select_related("consumer").order_by("-created_at")
    return render(request, "consumer/product_detail.html", {
        "product": product,
        "reviews": reviews,
    })
