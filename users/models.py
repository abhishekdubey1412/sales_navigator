# yourapp/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class UserProfile(AbstractUser):
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='avatars/', blank=True, null=True, default="avatars/default_image.jpg")
    company_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    total_scraping = models.IntegerField(default=1)

    # Ensure email is unique and required
    email = models.EmailField(unique=True, blank=False, null=False)


    def __str__(self):
        return self.username