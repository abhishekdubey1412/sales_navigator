import random
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from users.models import UserProfile
from django.http import JsonResponse
from core.models import WebsiteDetails
from sales_navigator.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from subscriptions.models import Package, SubscriptionPlan
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404

# Sign In view
@csrf_exempt
def sign_in(request):
    # Redirect authenticated users to the home page
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email, password = request.POST.get('email'), request.POST.get('password')
        if email and password:
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                return JsonResponse({'success': True, 'redirect_url': request.POST.get('redirect_url', '/')})
            return JsonResponse({'success': False, 'message': 'Invalid email or password.'})
        return JsonResponse({'success': False, 'message': 'Both email and password are required.'})
    return render(request, 'authentication/sign-in.html')

# Sign Out view
@login_required(login_url='sign_in')
def sign_out(request):
    # Log out the user
    logout(request)

    # Clear cookies
    response = redirect('/accounts/logout/')
    for cookie in request.COOKIES.keys():
        response.delete_cookie(cookie)

    # Optionally, clear the session
    request.session.flush()

    return response

# OTP Generator function
def generate_otp():
    # Generate a 6-digit OTP
    return str(random.randint(100000, 999999))

# Sign Up view
@csrf_exempt
def sign_up(request):
    # Redirect authenticated users to the home page
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email, phone, password, confirm_password = (request.POST.get(field) for field in ('email', 'phone', 'password', 'confirm-password'))
        if email and phone and password and confirm_password:
            if password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match.'})
            if UserProfile.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email already exists.'})
            request.session['user_data'] = {'email': email, 'phone': phone, 'password': password}
            otp = generate_otp()
            request.session['otp'] = otp
            try:
                send_mail(subject='Your OTP Code', to_email=email, context={'username': email, 'otp': otp, "website_logo": WebsiteDetails.objects.first().small_light_logo, "thank_you_image": request.build_absolute_uri("/static/assets/media/email/icon-positive-vote-1.svg"), "website_name": WebsiteDetails.objects.first().website_name, "website_url": request.build_absolute_uri("/"),}, mail_type="otp-email")
                return JsonResponse({'success': True, 'redirect_url': '/otp-verification/'})
            except Exception:
                return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
        return JsonResponse({'success': False, 'message': 'Please fill in all fields.'})
    return render(request, 'authentication/sign-up.html')

# OTP Verification view
@csrf_exempt
def otp_verification(request):
    user_data = request.session.get('user_data')
    if not user_data:
        return redirect('home')
    if request.method == 'POST':
        otp_input = ''.join([request.POST.get(f'code_{i}', '') for i in range(1, 7)])
        if otp_input == request.session.get('otp'):
            user = UserProfile.objects.create(
                username=user_data['email'].split('@')[0], email=user_data['email'],
                mobile_no=user_data['phone'], password=make_password(user_data['password'])
            )
            user = authenticate(request, email=user_data['email'], password=user_data['password'])
            request.session.pop('user_data', None)
            request.session.pop('otp', None)
            if user:
                selected_plan = get_object_or_404(SubscriptionPlan, name='free')
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
                login(request, user)
                return JsonResponse({'success': True, 'redirect_url': '/'})
            return JsonResponse({'success': False, 'message': 'Session expired. Please sign up again.'})
        return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})
    return render(request, 'authentication/two-factor.html', {'mail': f"{user_data['email'][:4] + '*' * (len(user_data['email'].split('@')[0]) - 4)}@{user_data['email'].split('@')[1]}"})

# Resend OTP view
def resend_otp(request):
    user_data = request.session.get('user_data')
    if not user_data:
        messages.error(request, 'Session expired. Please sign up again.')
        return redirect('otp_verification')
    otp = generate_otp()
    request.session['otp'] = otp
    try:
        send_mail(subject='Your OTP Code', to_email=user_data['email'], context={'username': user_data['email'], 'otp': otp, "website_logo": WebsiteDetails.objects.first().small_light_logo, "thank_you_image": request.build_absolute_uri("/static/assets/media/email/icon-positive-vote-1.svg"), "website_url": request.build_absolute_uri("/")}, mail_type="otp-email")
        messages.success(request, 'New OTP resent successfully.')
    except Exception:
        messages.error(request, 'Failed to resend OTP. Please try again.')
    return redirect('otp_verification')

# Reset Password view
@csrf_exempt
def reset_password(request):
    # Redirect authenticated users to the home page
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email, phone = request.POST.get('email'), request.POST.get('phone')
        if email and phone:
            user = UserProfile.objects.filter(email=email, mobile_no=phone).first()
            if user:
                otp = generate_otp()
                request.session['otp'] = otp
                request.session['user_data'] = {'email': email, 'phone': phone}
                reset_link = request.build_absolute_uri(f'/new-password/?otp={otp}')
                try:
                    send_mail(subject='Password Reset OTP', to_email=email, context={'otp': otp, 'reset_link': reset_link}, mail_type="reset-otp-email")
                    return JsonResponse({'success': True, 'redirect_url': '/'})
                except Exception:
                    return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
            return JsonResponse({'success': False, 'message': 'User with provided email and phone does not exist.'})
        return JsonResponse({'success': False, 'message': 'Please fill in all fields.'})
    return render(request, 'authentication/reset-password.html')

# New Password view
@csrf_exempt
def new_password(request):
    # Redirect authenticated users to the home page
    if request.user.is_authenticated:
        return redirect('/')
    otp = request.GET.get('otp')
    if not otp:
        return redirect('home')
    if request.method == 'POST':
        new_password, confirm_password = request.POST.get('password'), request.POST.get('confirm-password')
        if otp != request.session.get('otp'):
            return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})
        if not new_password or not confirm_password:
            return JsonResponse({'success': False, 'message': 'Please fill in all fields.'})
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match.'})
        user_data = request.session.get('user_data')
        if user_data:
            try:
                user = UserProfile.objects.get(email=user_data['email'], mobile_no=user_data['phone'])
                user.set_password(new_password)
                user.save()
                user = authenticate(request, email=user.email, password=new_password)
                request.session.pop('user_data', None)
                request.session.pop('otp', None)
                if user:
                    login(request, user)
                return JsonResponse({'success': True, 'redirect_url': '/'})
            except UserProfile.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found.'})
    return render(request, 'authentication/new-password.html', {'otp': otp})