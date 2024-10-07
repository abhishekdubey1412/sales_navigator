from datetime import timedelta
from core.models import WebsiteDetails
from scraping.models import ScrapingType
from django.http import HttpResponseForbidden
from .models import SubscriptionStatus, Package
from subscriptions.models import SubscriptionPlan
from django.shortcuts import render, redirect, get_object_or_404

def get_common_context(request):
    return {
        "active_package": Package.objects.filter(user=request.user, status="active").first(),
        "scraping_types": ScrapingType.objects.all(),
        "website_details": WebsiteDetails.objects.first(),
        "subscription_status": SubscriptionStatus.objects.all()
    }

def subscription_request(request):
    if request.user.is_staff:
        return render(request, 'subscription/subscription-request.html', get_common_context(request))
    return redirect('home')

def subscription_approved(request):
    if request.user.is_superuser:
        return render(request, 'subscription/subscription-approved.html', get_common_context(request))
    return redirect('home')

def action_approve(request):
    if not (request.user.is_superuser or request.user.is_staff) or request.method != "POST":
        return HttpResponseForbidden()

    subscription_status = get_object_or_404(SubscriptionStatus, pk=request.POST.get('subscription_id'))
    subscription_status.approved_by = request.user
    subscription_status.status = 'active'
    subscription_status.save()

    selected_plan = get_object_or_404(SubscriptionPlan, name=subscription_status.package_name)
    current_package = Package.objects.filter(user=subscription_status.user, status='active').first()
    new_package_data = {
        'user': subscription_status.user,
        'name': subscription_status.package_name,
        'monthly_or_annually': subscription_status.monthly_or_annually,
        'status': 'active',
        'created_at': subscription_status.updated_at,
        'scraping_slots': selected_plan.scraping_slots,
        'price': subscription_status.billing,
        'active_until': subscription_status.updated_at + timedelta(days=30) if subscription_status.monthly_or_annually == 'monthly' else subscription_status.updated_at + timedelta(days=365),
        **{field.name: getattr(selected_plan, field.name) for field in SubscriptionPlan._meta.fields if field.name not in ['id', 'name', 'monthly_price', 'annual_price']}
    }

    if current_package and current_package.name != "free":
        for field in ['execution_time_hours', 'ai_credits_per_month', 'find_email_credits', 'direct_number_credits', 'mobile_number_credits', 'lead_location_phone_number_credits', 'lead_location_address_credits', 'company_hq_number_credits', 'company_hq_address_credits', 'company_revenue_credits', 'export_leads_limit', 'export_accounts_limit']:
            new_package_data[field] += getattr(current_package, field)
        new_package_data['ai_credits_per_month'] -= current_package.used_credit
        current_package.status = 'expired'
        current_package.save()
    
    Package.objects.create(**new_package_data)
    if current_package:
        current_package.status = 'expired'
        current_package.save()
        
    return redirect(request.META.get('HTTP_REFERER', '/'))

def action_reject(request):
    if (request.user.is_superuser or request.user.is_staff) and request.method == "POST":
        subscription_status = get_object_or_404(SubscriptionStatus, pk=request.POST.get('subscription_id'))
        subscription_status.approved_by = request.user
        subscription_status.status = 'canceled'
        subscription_status.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseForbidden()
