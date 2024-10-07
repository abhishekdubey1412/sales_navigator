from django.contrib import admin
from .models import SubscriptionPlan, Package, SubscriptionStatus

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'monthly_price', 
        'annual_price', 
        'execution_time_hours', 
        'ai_credits_per_month', 
        'scraping_slots', 
        'unlimited_export', 
        'priority_support',
        'export_leads_limit',
        'export_accounts_limit',
    )
    search_fields = ('name',)
    list_filter = (
        'unlimited_export',
        'priority_support',
        'basic_filters',
        'advanced_filters',
    )
    ordering = ('name',)

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'name', 
        'monthly_or_annually', 
        'status', 
        'price', 
        'execution_time_hours', 
        'ai_credits_per_month', 
        'used_credit', 
        'scraping_slots', 
        'used_slots', 
        'unlimited_export', 
        'priority_support', 
        'credits_rollover', 
        'find_email_credits', 
        'direct_number_credits', 
        'mobile_number_credits', 
        'lead_location_phone_number_credits', 
        'lead_location_address_credits', 
        'company_hq_number_credits', 
        'company_hq_address_credits', 
        'company_revenue_credits', 
        'basic_filters', 
        'advanced_filters', 
        'export_leads_limit', 
        'export_accounts_limit', 
        'clean_data', 
        'created_at', 
        'active_until',
    )
    search_fields = ('name', 'user__username', 'status')
    list_filter = (
        'status', 
        'monthly_or_annually', 
        'unlimited_export', 
        'priority_support', 
        'credits_rollover', 
        'basic_filters', 
        'advanced_filters', 
        'clean_data',
    )
    ordering = ('name',)

@admin.register(SubscriptionStatus)
class SubscriptionStatusAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'status', 
        'billing', 
        'package_name', 
        'monthly_or_annually', 
        'created_at', 
        'updated_at', 
        'approved_by',
    )
    search_fields = ('user__username', 'status', 'package_name')
    list_filter = (
        'status', 
        'monthly_or_annually', 
        'created_at', 
        'updated_at',
    )
    ordering = ('-created_at',)