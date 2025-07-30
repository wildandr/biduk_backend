from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    """
    Admin panel untuk model User kustom
    """
    list_display = ('username', 'email', 'full_name', 'phone_number', 'is_staff', 'is_admin', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_admin', 'is_active')
    search_fields = ('username', 'email', 'full_name', 'phone_number')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'full_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'password1', 'password2'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
