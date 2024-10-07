from django.contrib import admin
from .models import UserProfile
from django.contrib.auth.models import Group

class UserProfileAdmin(admin.ModelAdmin):
    model = UserProfile
    list_display = (
        'username', 
        'email', 
        'is_active', 
        'is_staff', 
        'is_superuser', 
        'last_login', 
        'date_joined'
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

# Register the custom user admin
admin.site.register(UserProfile, UserProfileAdmin)

admin.site.unregister(Group)  # Corrected this line