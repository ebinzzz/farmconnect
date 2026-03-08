"""FarmConnect – Root URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/auth/login/"), name="home"),
    path("django-admin/", admin.site.urls),
    path("auth/",     include("apps.accounts.urls",   namespace="accounts")),
    path("farmer/",   include("apps.farmers.urls",    namespace="farmers")),
    path("consumer/", include("apps.consumers.urls",  namespace="consumers")),
    path("products/", include("apps.products.urls",   namespace="products")),
    path("orders/",   include("apps.orders.urls",     namespace="orders")),
    path("reviews/",  include("apps.reviews.urls",    namespace="reviews")),
    path("admin-panel/", include("apps.adminpanel.urls", namespace="adminpanel")),
    path("dashboard/", include("apps.accounts.dashboard_urls", namespace="dashboard")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
