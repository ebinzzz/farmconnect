# farmers/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def farmer_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not request.user.is_farmer:
            messages.error(request, "Access restricted to farmers.")
            return redirect("farmers:dashboard")
        return view_func(request, *args, **kwargs)
    return _wrapped
