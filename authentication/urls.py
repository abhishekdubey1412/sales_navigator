from django.urls import path
from . import views

urlpatterns = [
    path('sign-in/', views.sign_in, name='sign_in'),
    path('sign-out/', views.sign_out, name='sign_out'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('otp-verification/', views.otp_verification, name='otp_verification'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('new-password/', views.new_password, name='new_password'),
]