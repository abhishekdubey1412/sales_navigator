import requests
from user_agents import parse
from django.conf import settings
from django.http import HttpRequest
from django.dispatch import receiver
from .models import LoginSession, UserLogEntry
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in
   
class UserActionLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        # Check if the request is for static or media files
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            # Skip logging for static and media files
            return self.get_response(request)

        # Get the response
        response = self.get_response(request)

        # Log the action if the user is authenticated
        if request.user.is_authenticated:
            UserLogEntry.objects.create(
                user=request.user,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
            )

        return response

class LoginSessionMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    @staticmethod
    @receiver(user_logged_in)
    def log_user_login(sender, request, user, **kwargs):
        """Log the user login event."""
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0]  # Get the first IP if there are multiple
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        location_data = LoginSessionMiddleware.get_location(ip_address)
        device_info = LoginSessionMiddleware.get_device_info(request.META.get('HTTP_USER_AGENT', 'unknown'))

        LoginSession.objects.create(
            user=user,
            location=location_data.get('country', 'Unknown') if location_data else 'Unknown',
            status="OK",  # Set as needed
            device=device_info,
            ip_address=ip_address,
            city=location_data.get('city', None),
            region=location_data.get('region', None),
        )

    @staticmethod
    def get_location(ip_address):
        """Fetch location data from ipinfo.io."""
        try:
            response = requests.get(f'https://ipinfo.io/{ip_address}/json')
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                }
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def get_device_info(user_agent):
        """Extract and format device and browser info from user agent."""
        user_agent_parsed = parse(user_agent)
        
        browser = user_agent_parsed.browser.family
        os = user_agent_parsed.os.family
        
        if user_agent_parsed.is_mobile:
            device = user_agent_parsed.device.family
            return f"{browser} - {os}, {device} - Mobile"
        elif user_agent_parsed.is_tablet:
            device = user_agent_parsed.device.family
            return f"{browser} - {os}, {device} - Tablet"
        else:
            return f"{browser} - {os}"