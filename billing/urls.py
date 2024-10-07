from django.urls import path
from . import views

urlpatterns = [
    path('upgrade-plan/', views.upgrade_plan, name="upgrade_plan")
]
