from django.urls import path
from . import views
urlpatterns = [
    path('subscription-request/', views.subscription_request, name="subscription_request"),
    path('subscription-approved/', views.subscription_approved, name="subscription_approved"),
    path('action-approve/', views.action_approve, name="action_approve"),
    path('action-reject/', views.action_reject, name="action_reject"),
]