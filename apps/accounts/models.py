"""
accounts/models.py
Custom User model with role-based access: FARMER | CONSUMER | ADMIN
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.ADMIN)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    FARMER   = "farmer"
    CONSUMER = "consumer"
    ADMIN    = "admin"
    ROLE_CHOICES = [
        (FARMER,   "Farmer"),
        (CONSUMER, "Consumer"),
        (ADMIN,    "Admin"),
    ]

    email      = models.EmailField(unique=True)
    full_name  = models.CharField(max_length=150)
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CONSUMER)
    phone      = models.CharField(max_length=15, blank=True)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    avatar     = models.ImageField(upload_to="avatars/", blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "fc_users"
        verbose_name = "User"

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def is_farmer(self):
        return self.role == self.FARMER

    @property
    def is_consumer(self):
        return self.role == self.CONSUMER

    @property
    def is_admin_user(self):
        return self.role == self.ADMIN
