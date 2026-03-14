from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "language", "timezone")
    readonly_fields = ("date_joined",)