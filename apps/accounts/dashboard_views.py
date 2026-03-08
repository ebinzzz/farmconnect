from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_home(request):
    user = request.user
    if user.is_farmer:
        return redirect("farmers:dashboard")
    elif user.is_consumer:
        return redirect("consumers:dashboard")
    elif user.is_agent:
        return redirect("orders:agent_dashboard")
    elif user.is_admin_user or user.is_staff:
        return redirect("adminpanel:dashboard")
    return redirect("accounts:login")
