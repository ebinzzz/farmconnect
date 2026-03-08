from django.urls import path
from . import views

app_name = "farmers"

urlpatterns = [
    path("dashboard/",           views.dashboard,      name="dashboard"),
    path("products/add/",        views.product_add,    name="product_add"),
    path("products/<int:pk>/edit/",   views.product_edit,   name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("categories/",          views.category_list,   name="category_list"),
    path("categories/add/",      views.category_add,    name="category_add"),
    path("categories/<int:pk>/edit/", views.category_edit,  name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("orders/",              views.order_list,     name="order_list"),
    path("orders/<int:pk>/",     views.order_detail,   name="order_detail"),
    
    # Agent Management
    path("agents/",              views.agent_list,     name="agent_list"),
    path("agents/add/",          views.agent_add,      name="agent_add"),
    path("agents/<int:pk>/edit/", views.agent_edit,    name="agent_edit"),
    path("agents/<int:pk>/delete/", views.agent_delete, name="agent_delete"),
    path("agents/<int:pk>/orders/", views.agent_orders, name="agent_orders"),
]
