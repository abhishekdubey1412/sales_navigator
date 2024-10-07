from django.db import models
from datetime import timedelta
from django.utils import timezone
from subscriptions.models import Package, SubscriptionPlan

class ExpiredPackageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            
            # Handle expired packages
            expired_packages = Package.objects.filter(user=request.user, active_until__lt=now, status='active', monthly_or_annually='monthly')
            expired_packages.update(status='expired')

            # Handle annual packages
            annual_packages = Package.objects.filter(
                user=request.user,
                status='active',
                monthly_or_annually='annual',
            )

            for package in annual_packages:

                if package.active_until < now:
                    package.status = 'expired'
                    package.created_at = package.active_until - timedelta(days=365)
                    package.save()
                else:
                    # Add SubscriptionPlan data after 30 days
                    try:
                        subscription_plan = SubscriptionPlan.objects.get(name=package.name)
                        for field in ['execution_time_hours', 'ai_credits_per_month', 'find_email_credits', 
                                      'direct_number_credits', 'mobile_number_credits', 'lead_location_phone_number_credits', 
                                      'lead_location_address_credits', 'company_hq_number_credits', 'company_hq_address_credits', 
                                      'company_revenue_credits', 'export_leads_limit', 'export_accounts_limit']:
                            if hasattr(package, field) and hasattr(subscription_plan, field):
                                setattr(package, field, getattr(package, field) + getattr(subscription_plan, field))
                        
                        # Handle boolean fields
                        for field in ['unlimited_export', 'priority_support', 'credits_rollover', 'basic_filters', 'advanced_filters', 'clean_data']:
                            if hasattr(package, field) and hasattr(subscription_plan, field):
                                setattr(package, field, getattr(package, field) or getattr(subscription_plan, field))
                        
                        # Subtract used credits
                        package.ai_credits_per_month -= package.used_credit
                        package.created_at = now
                        package.used_credit = 0
                        package.save()
                    except SubscriptionPlan.DoesNotExist:
                        # Handle the case where the SubscriptionPlan doesn't exist
                        pass

        # Process the request
        response = self.get_response(request)
        return response