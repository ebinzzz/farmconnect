from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/",                         views.cart_view,           name="cart"),
    path("cart/add/<int:product_id>/",    views.add_to_cart,         name="add_to_cart"),
    path("cart/remove/<int:item_id>/",    views.remove_from_cart,    name="remove_from_cart"),
    path("checkout/",                     views.checkout,            name="checkout"),
    path("",                              views.order_list,          name="order_list"),
    path("<int:pk>/",                     views.order_detail,        name="order_detail"),
    path("<int:pk>/status/",              views.update_order_status, name="update_status"),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('payment/verify/',               views.verify_payment,      name='verify_payment'),
    path('<int:pk>/cancel/',              views.cancel_order,        name='cancel_order'),

    # Delivery Agent
    path('agent/dashboard/',              views.agent_dashboard,     name='agent_dashboard'),
    path('agent/history/',                views.agent_history,       name='agent_history'),
]
