from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("",                            views.dashboard,          name="dashboard"),
    path("users/",                      views.user_list,          name="user_list"),
    path("users/<int:pk>/toggle/",      views.toggle_user_active, name="toggle_user"),
    path("products/",                   views.product_list,       name="product_list"),
    path("orders/",                     views.order_list,         name="order_list"),
]
