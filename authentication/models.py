from django.db import models
from users.models import UserProfile

# Create your models here.
class LoginSession(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    location = models.CharField(max_length=100)  # Country
    status = models.CharField(max_length=10)      # OK, ERR, WRN
    device = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # Optional fields for detailed location
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.location} - {self.status} - {self.device} - {self.timestamp}"

class UserLogEntry(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    status_code = models.IntegerField()

    def __str__(self):
        return f"{self.timestamp} - {self.user.username} - {self.method} {self.path} - {self.status_code}"