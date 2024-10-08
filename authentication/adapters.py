# adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import login
from .models import UserProfile

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email')
        
        if email:
            try:
                # Check if the email exists in the UserProfile model
                user_profile = UserProfile.objects.get(email=email)
                sociallogin.connect(request, user_profile)  # Connect the social login
                login(request, user_profile, backend='authentication.backends.EmailBackend')  # Log in the user
            except UserProfile.DoesNotExist:
                # Proceed with the normal flow if no UserProfile is found
                pass