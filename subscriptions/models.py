from django.db import models
from datetime import timedelta
from django.utils import timezone
from users.models import UserProfile

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('team', 'Team'),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    execution_time_hours = models.DurationField()
    ai_credits_per_month = models.IntegerField()
    scraping_slots = models.IntegerField()
    unlimited_export = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    credits_rollover = models.BooleanField(default=True)
    find_email_credits = models.IntegerField()
    direct_number_credits = models.IntegerField()
    mobile_number_credits = models.IntegerField()
    lead_location_phone_number_credits = models.IntegerField()
    lead_location_address_credits = models.IntegerField()
    company_hq_number_credits = models.IntegerField()
    company_hq_address_credits = models.IntegerField()
    company_revenue_credits = models.IntegerField()
    basic_filters = models.BooleanField(default=True)
    advanced_filters = models.BooleanField(default=False)
    export_leads_limit = models.IntegerField()
    export_accounts_limit = models.IntegerField()
    clean_data = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return self.name
    
class Package(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="Need To Plan")
    MONTHLY_ANNUAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annually'),
        ('14_days', '14 Days'),
    ]
     
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ]
    monthly_or_annually = models.CharField(max_length=10, choices=MONTHLY_ANNUAL_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    execution_time_hours = models.DurationField(default=timezone.timedelta(0))
    ai_credits_per_month = models.IntegerField(default=0)
    used_credit = models.IntegerField(default=0)
    scraping_slots = models.IntegerField(default=0)
    used_slots = models.IntegerField(default=0)
    unlimited_export = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    credits_rollover = models.BooleanField(default=False)
    find_email_credits = models.IntegerField(default=0)
    direct_number_credits = models.IntegerField(default=0)
    mobile_number_credits = models.IntegerField(default=0)
    lead_location_phone_number_credits = models.IntegerField(default=0)
    lead_location_address_credits = models.IntegerField(default=0)
    company_hq_number_credits = models.IntegerField(default=0)
    company_hq_address_credits = models.IntegerField(default=0)
    company_revenue_credits = models.IntegerField(default=0)
    basic_filters = models.BooleanField(default=False)
    advanced_filters = models.BooleanField(default=False)
    export_leads_limit = models.IntegerField(default=0)
    export_accounts_limit = models.IntegerField(default=0)
    clean_data = models.BooleanField(default=False)
    created_at = models.DateTimeField(blank=True, null=True)
    active_until = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user}) - Status: {self.get_status_display()}"
    
class SubscriptionStatus(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='requested_user')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='pending', blank=True)
    billing = models.CharField(max_length=100, blank=True)
    package_name = models.CharField(max_length=100, blank=True)
    monthly_or_annually = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_by_staff')

    def save(self, *args, **kwargs):
        if self.status != 'pending':
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.package_name} ({self.status})"