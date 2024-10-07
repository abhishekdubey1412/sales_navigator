from django.contrib import admin
from .models import BillingHistory, Statement

@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'date', 'description', 'amount')
    search_fields = ('user__username', 'package', 'description')
    list_filter = ('date', 'package')

@admin.register(Statement)
class StatementAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'order_id', 'details', 'credit')
    search_fields = ('user__username', 'order_id', 'details')
    list_filter = ('date',)