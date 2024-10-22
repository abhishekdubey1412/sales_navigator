import threading
from django.conf import settings
from sales_navigator.mail import send_mail
from .models import WebsiteDetails, ContactUs
from django.shortcuts import render, redirect
from django.db.models import IntegerField, Case, When
from scraping.models import ScrapingType, ScrapingInfo
from django.contrib.auth.decorators import login_required
from subscriptions.models import Package, SubscriptionPlan

def get_common_context(request):
    return {
        "active_package": Package.objects.filter(user=request.user, status="active").first(),
        "scraping_types": ScrapingType.objects.all(),
        "website_details": WebsiteDetails.objects.first(),
    }

# home Page
@login_required(login_url='sign_in')
def home(request):
    context = get_common_context(request)
    context["subscription_plans"] = SubscriptionPlan.objects.all().order_by(Case(
                When(name='free', then=1),
                When(name='basic', then=2),
                When(name='professional', then=3),
                When(name='team', then=4),
                output_field=IntegerField(),
            ))
    context["total_seconds"] = context["active_package"].execution_time_hours.total_seconds() if context["active_package"] else 0
    context["scraping_infos"] = ScrapingInfo.objects.filter(email=request.user.email).order_by('-starting_time')
    return render(request, 'index.html', context)

# Contact Us page
@login_required()
def contact(request):
    if request.method == "POST":
        name    = request.POST.get("name", '')
        email   = request.POST.get("email", '')
        subject = request.POST.get("subject", '')
        message = request.POST.get("message", '')

        contact_us = ContactUs(name=name, email=email, subject=subject, message=message)
        contact_us.save()


        context ={
            "website_logo": WebsiteDetails.objects.first().small_light_logo.url,
            "thank_you_image": request.build_absolute_uri("/static/assets/media/email/icon-positive-vote-1.svg"),
            "website_name": WebsiteDetails.objects.first().website_name,
            "website_url": request.build_absolute_uri("/"),
        }

        # Send email to user
        mail_thread = threading.Thread(target=send_mail, args=( "Thank you for contacting us!", email, context, "contact-us-user" ))
        mail_thread.start()

        context ={
            "website_logo": WebsiteDetails.objects.first().small_light_logo.url,
            "thank_you_image": request.build_absolute_uri("/static/assets/media/email/icon-positive-vote-1.svg"),
            "website_name": WebsiteDetails.objects.first().website_name,
            "website_url": request.build_absolute_uri("/"),
            "user_name": name,
            "user_email": email,
            "message": message,
            "subject": subject,
        }

        # Send email to admin
        mail_thread = threading.Thread(target=send_mail, args=( "New Contact Us Form Submission", settings.DEFAULT_FROM_EMAIL, context, "contact-us-admin" ))
        mail_thread.start()


        return redirect("thank_you")
    
    return render(request, 'contact.html', get_common_context(request))

# Thank You Page
@login_required(login_url='sign_in')
def thank_you(request):
    return render(request, 'thank-you.html', get_common_context(request))

# FAQs Page
@login_required(login_url='sign_in')
def faqs(request):
    return render(request, 'faqs.html', get_common_context(request))

# Terms & Conditions Page
def terms_and_conditions(request):
    return render(request, 'terms-and-conditions.html', {"website_details": WebsiteDetails.objects.first()})

# Filter Page
@login_required(login_url='sign_in')
def filter_page(request):
    return render(request, 'filtered.html', get_common_context(request))