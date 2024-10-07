from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from subscriptions.models import SubscriptionPlan, SubscriptionStatus
from billing.models import BillingHistory
from django.contrib.auth.decorators import login_required
import json

@login_required
def upgrade_plan(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            package_name = data.get('Package', '')
            selected_plan = get_object_or_404(SubscriptionPlan, name=package_name)
            is_annual = data.get('selectedPlan', '').lower() == "annual"
            price = selected_plan.annual_price if is_annual else selected_plan.monthly_price
            SubscriptionStatus.objects.create(
                user=request.user, billing=price, package_name=package_name,
                monthly_or_annually="monthly" if not is_annual else "annual"
            )
            BillingHistory.objects.create(
                user=request.user, package=package_name,
                description=f'Package upgrade to {package_name}', amount=price
            )
            return JsonResponse({'success': True, 'message': 'Plan upgraded successfully!'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)