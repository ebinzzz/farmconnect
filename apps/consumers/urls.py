from django.urls import path
from . import views

app_name = "consumers"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]
