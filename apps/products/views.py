from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category

def product_list(request):
    products = Product.objects.filter(is_available=True)
    
    query = request.GET.get("q")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        
    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)
        
    min_price = request.GET.get("min_price")
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
            
    max_price = request.GET.get("max_price")
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    categories = Category.objects.all()

    # SWITCH TEMPLATE BASED ON ROLE
    template_name = "product_list.html"
    if request.user.is_authenticated and getattr(request.user, "is_consumer", False):
        template_name = "consumer/product_list.html"

    return render(request, template_name, {
        "products": products,
        "categories": categories,
        "query": query,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related = Product.objects.filter(category=product.category, is_available=True).exclude(pk=pk)[:4]
    return render(request, "product_detail.html", {
        "product": product,
        "related_products": related,
    })
