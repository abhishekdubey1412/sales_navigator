from .models import UserProfile
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from billing.models import Statement
from core.models import WebsiteDetails
from scraping.models import ScrapingType
from billing.models import BillingHistory
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db.models import IntegerField, Case, When
from django.contrib.auth.decorators import login_required
from subscriptions.models import SubscriptionPlan, Package
from authentication.models import LoginSession, UserLogEntry
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, update_session_auth_hash

def get_common_context(request):
    return {
        'scraping_types': ScrapingType.objects.all(),
        'website_details': WebsiteDetails.objects.first(),
        'active_package': Package.objects.filter(user=request.user, status="active").first()
    }

@login_required(login_url='sign_in')
def overview(request):
    return render(request, 'user-profile/overview.html', get_common_context(request))

@login_required(login_url='sign_in')
def settings(request):
    return render(request, 'user-profile/settings.html', get_common_context(request))

@login_required(login_url='sign_in')
def update_profile(request):
    if request.method == "POST":
        user = request.user
        if 'avatar' in request.FILES:
            user.profile_image = request.FILES['avatar']
        user.first_name = request.POST.get('fname')
        user.last_name = request.POST.get('lname')
        user.mobile_no = request.POST.get('phone')
        user.company_name = request.POST.get('company_name')
        user.tax_id = request.POST.get('TaxID')
        user.address = request.POST.get('address')
        user.country = request.POST.get('country')
        user.save()
        return redirect('overview')

@login_required(login_url='sign_in')
def update_email(request):
    if request.method == "POST":
        email = request.POST.get('emailaddress')
        password = request.POST.get('confirmemailpassword')
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'success': False, 'message': 'Invalid email address.'})
        user = request.user
        if email and email != user.email and UserProfile.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'This email address is already in use.'})
        user = authenticate(request, email=user.email, password=password)
        if user is None:
            return JsonResponse({'success': False, 'message': 'Incorrect password.'})
        user.email = email
        user.username = email.split('@')[0]
        user.save()
        return JsonResponse({'success': True, 'message': 'Email address updated successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required(login_url='sign_in')
def change_password(request):
    if request.method == "POST":
        current_password = request.POST.get('currentpassword')
        new_password = request.POST.get('newpassword')
        confirm_password = request.POST.get('confirmpassword')
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'New passwords do not match.'})
        user = authenticate(request, email=request.user.email, password=current_password)
        if user is None:
            return JsonResponse({'success': False, 'message': 'Current password is incorrect.'})
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return JsonResponse({'success': True, 'message': 'Password updated successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required(login_url='sign_in')
def billing(request):
    context = get_common_context(request)
    context.update({
        'subscription_plans': SubscriptionPlan.objects.all().order_by(
            Case(
                When(name='free', then=1),
                When(name='basic', then=2),
                When(name='professional', then=3),
                When(name='team', then=4),
                output_field=IntegerField(),
            )
        ),
        'billing_history_all': BillingHistory.objects.filter(user=request.user),
        'billing_history_months': BillingHistory.objects.filter(user=request.user).filter(date__month=timezone.now().month),
        'billing_history_year': BillingHistory.objects.filter(user=request.user).filter(date__year=timezone.now().year),
        'used_percent': (context['active_package'].used_credit / context['active_package'].ai_credits_per_month) * 100 if context['active_package'] and context['active_package'].ai_credits_per_month > 0 else 0
    })
    return render(request, 'user-profile/billing.html', context)

@login_required(login_url='sign_in')
def statements(request):
    context = get_common_context(request)
    context.update({
        'statements': Statement.objects.filter(user=request.user).order_by('-date')
    })
    return render(request, 'user-profile/statements.html', context)

@login_required(login_url='sign_in')
def api_keys(request):
    return render(request, 'user-profile/api-keys.html', get_common_context(request))

@login_required(login_url='sign_in')
def logs(request):
    context = get_common_context(request)
    context.update({
        'sessions': LoginSession.objects.filter(user=request.user).order_by('-timestamp'),
        'log_entries': UserLogEntry.objects.filter(user=request.user).order_by('-timestamp')
    })
    return render(request, 'user-profile/logs.html', context)

@login_required(login_url='sign_in')
def dashboard(request):
    if request.user.is_superuser:
        context = get_common_context(request)
        context.update({'users': UserProfile.objects.all()})
        return render(request, 'user-management/dashboard.html', context)
    return redirect('home')

@login_required(login_url='sign_in')
def users_list(request):
    if request.user.is_superuser:
        context = get_common_context(request)
        context.update({'users': UserProfile.objects.all()})
        return render(request, 'user-management/user-lists.html', context)
    return redirect('home')

@csrf_exempt
def add_user(request):
    if request.user.is_superuser and request.method == 'POST':
        email = request.POST.get('user_email')
        password = request.POST.get('password')
        role = request.POST.get('user_role')
        avatar = request.FILES.get('avatar')
        if not email or UserProfile.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email is already in use or invalid.'}, status=400)
        if any(check_password(password, user.password) for user in UserProfile.objects.all()):
            return JsonResponse({'error': 'Password already in use. Please choose a different password.'}, status=400)
        username = email.split('@')[0]
        user = UserProfile(username=username, email=email, password=make_password(password))
        user.is_staff = role in ['0', '1']
        user.is_superuser = role == '0'
        if avatar:
            user.profile_image = avatar
        user.save()
        return JsonResponse({'message': 'User has been successfully created!'}, status=201)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='sign_in')
def update_role(request):
    if request.user.is_superuser and request.method == "POST":
        user = get_object_or_404(UserProfile, pk=request.POST.get('user_id'))
        role = request.POST.get('user_role')
        user.is_staff = role in ['0', '1']
        user.is_superuser = role == '0'
        user.save()
        messages.success(request, 'User role updated successfully.')
        return redirect('users_list')
    messages.error(request, 'Invalid request method.')
    return redirect('users_list')

@login_required(login_url='sign_in')
def user_activate(request, user_id):
    if request.user.is_superuser:
        user = get_object_or_404(UserProfile, pk=user_id)
        user.is_active = True
        user.save()
        messages.success(request, 'User successfully activated.')
        return redirect('users_list')

@login_required(login_url='sign_in')
def user_deactivate(request, user_id):
    if request.user.is_superuser:
        user = get_object_or_404(UserProfile, pk=user_id)
        user.is_active = False
        user.save()
        messages.success(request, 'User successfully deactivated.')
        return redirect('users_list')

@login_required(login_url='sign_in')
def roles(request):
    if request.user.is_superuser:
        return render(request, 'user-management/roles.html', get_common_context(request))
    return redirect('home')

@login_required(login_url='sign_in')
def user_role(request):
    if request.user.is_superuser and request.method == 'GET':
        context = get_common_context(request)
        user_type = request.GET.get('user-type')
        user_filters = {
            "Administrator": {'is_superuser': True},
            "Staff": {'is_staff': True, 'is_superuser': False},
            "User": {'is_staff': False}
        }
        filter_criteria = user_filters.get(user_type)
        if filter_criteria:
            context.update({'user_type': user_type, 'user_infos': UserProfile.objects.filter(**filter_criteria)})
            return render(request, 'user-management/view.html', context)
        return redirect("roles")
    return redirect('home')

@login_required(login_url='sign_in')
def customization(request):
    if request.user.is_superuser:
        context = get_common_context(request)
        if request.method == 'POST':
            website_details = context['website_details']
            website_details.website_name = request.POST.get('wbname')
            for field in ['favicon', 'big_dark_logo', 'big_light_logo', 'small_light_logo', 'small_dark_logo']:
                if request.FILES.get(field):
                    setattr(website_details, field, request.FILES.get(field))
            website_details.save()
            return redirect('customization')
        return render(request, 'user-management/customization.html', context)
    return redirect('home')
