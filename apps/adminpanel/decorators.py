# adminpanel/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not (request.user.is_admin_user or request.user.is_staff):
            messages.error(request, "Admin access only.")
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)
    return _wrapped
