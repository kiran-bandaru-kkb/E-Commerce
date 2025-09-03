from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'is_admin', 'is_customer')
    list_filter = ('is_admin', 'is_customer')
    search_fields = ('username', 'email')
    ordering = ('-id',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_admin', 'is_customer')}),
    )


