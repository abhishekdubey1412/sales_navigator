from django.contrib import admin
from .models import WebsiteDetails

# Register your models here.
@admin.register(WebsiteDetails)
class WebsiteDetailsAdmin(admin.ModelAdmin):
    list_display = ('website_name', 'created_at', 'updated_at')
    search_fields = ('website_name',)
    ordering = ('created_at',)
    list_filter = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('website_name', 'favicon', 'big_dark_logo', 'big_light_logo', 'small_dark_logo', 'small_light_logo')
        }),
    )