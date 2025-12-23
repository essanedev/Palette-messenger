from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserContact

# Register your models here.


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_online', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_online']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {
            'fields': ('avatar', 'bio', 'phone', 'is_online', 'last_seen')
        }),
    )


@admin.register(UserContact)
class UserContactAdmin(admin.ModelAdmin):
    list_display = ['owner', 'contact', 'nickname', 'is_blocked', 'created_at']
    list_filter = ['is_blocked', 'created_at']
    search_fields = ['owner__username', 'contact__username']