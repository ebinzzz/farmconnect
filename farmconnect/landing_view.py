"""
farmconnect/landing_view.py
Put this file at the root of the project (same level as manage.py).
Then wire it in farmconnect/urls.py (see instructions at the bottom).
"""

from django.shortcuts import render
from apps.products.models import Product, Category
from apps.accounts.models import User


def landing(request):
    """
    Public landing page — no login required.
    Redirects authenticated users to their dashboard so they don't
    land here on every visit.
    """
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect("dashboard:home")

    featured_products = (
        Product.objects
        .filter(is_available=True, stock__gt=0)
        .select_related("farmer", "category")
        .order_by("-created_at")[:8]
    )

    categories = Category.objects.all()[:12]

    top_farmers = (
        User.objects
        .filter(role=User.FARMER, is_active=True)
        .prefetch_related("products")
        .order_by("-date_joined")[:5]
    )

    return render(request, "landing.html", {
        "featured_products": featured_products,
        "categories": categories,
        "top_farmers": top_farmers,
    })


# ─────────────────────────────────────────────────────────────────
# HOW TO WIRE THIS INTO farmconnect/urls.py
# ─────────────────────────────────────────────────────────────────
#
# 1. At the top of farmconnect/urls.py add:
#       from farmconnect.landing_view import landing
#
# 2. Change the existing root redirect line from:
#       path("", RedirectView.as_view(url="/auth/login/"), name="home"),
#    to:
#       path("", landing, name="home"),
#
# That's it! The landing page will show at / for unauthenticated
# visitors, and logged-in users are silently redirected to their
# dashboard.
# ─────────────────────────────────────────────────────────────────