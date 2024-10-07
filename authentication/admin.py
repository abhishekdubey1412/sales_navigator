from django.contrib import admin
from .models import LoginSession, UserLogEntry

@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'status', 'device', 'ip_address', 'timestamp', 'city', 'region')
    search_fields = ('user__username', 'location', 'status', 'device', 'ip_address', 'city', 'region')
    list_filter = ('status', 'location', 'timestamp')
    ordering = ('-timestamp',)

@admin.register(UserLogEntry)
class UserLogEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'method', 'path', 'status_code')
    search_fields = ('user__username', 'method', 'path', 'status_code')
    list_filter = ('method', 'status_code', 'timestamp')
    ordering = ('-timestamp',)
