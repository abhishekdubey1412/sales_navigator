import requests
from datetime import timedelta
from django.utils import timezone
from django.dispatch import receiver
from django.core.files.base import ContentFile
from django.contrib.auth.signals import user_logged_in
from allauth.socialaccount.models import SocialAccount
from subscriptions.models import Package, SubscriptionPlan

@receiver(user_logged_in)
def save_google_profile_picture(sender, request, user, **kwargs):
    # Check if the user has a Google social account
    social_account = SocialAccount.objects.filter(user=user, provider='google').first()
    
    if social_account:
        # Get the user's Google profile info
        social_data = social_account.extra_data
        picture_url = social_data.get('picture')

        if picture_url and str(user.profile_image) == "avatars/default_image.jpg":
            # Download the image from the URL
            response = requests.get(picture_url)
            if response.status_code == 200:
                # Save the image
                user.profile_image.save(f"{user.email}_profile_pic.jpg", ContentFile(response.content), save=True)
        
        # Check and save additional user data if not already present
        if not user.first_name:
            user.first_name = social_data.get('given_name', '')
        if not user.last_name:
            user.last_name = social_data.get('family_name', '')
        user.save()
    
    # Check if the user has a package
    if not Package.objects.filter(user=user, name='free').exists():
        selected_plan = SubscriptionPlan.objects.get(name='free')
        Package.objects.create(
            user=user, name='free', monthly_or_annually='14_days', status='active', price=0,
            execution_time_hours=selected_plan.execution_time_hours, ai_credits_per_month=selected_plan.ai_credits_per_month,
            scraping_slots=selected_plan.scraping_slots, unlimited_export=selected_plan.unlimited_export,
            priority_support=selected_plan.priority_support, credits_rollover=selected_plan.credits_rollover,
            find_email_credits=selected_plan.find_email_credits, direct_number_credits=selected_plan.direct_number_credits,
            mobile_number_credits=selected_plan.mobile_number_credits, lead_location_phone_number_credits=selected_plan.lead_location_phone_number_credits,
            lead_location_address_credits=selected_plan.lead_location_address_credits, company_hq_number_credits=selected_plan.company_hq_number_credits,
            company_hq_address_credits=selected_plan.company_hq_address_credits, company_revenue_credits=selected_plan.company_revenue_credits,
            basic_filters=selected_plan.basic_filters, advanced_filters=selected_plan.advanced_filters,
            export_leads_limit=selected_plan.export_leads_limit, export_accounts_limit=selected_plan.export_accounts_limit,
            clean_data=selected_plan.clean_data, created_at=timezone.now(), active_until=timezone.now() + timedelta(days=14)
        )