from django.db import models

# Create your models here.
class WebsiteDetails(models.Model):
    website_name = models.CharField(max_length=50, blank=True, null=True)
    favicon = models.FileField(upload_to='logos/', blank=True, null=True)
    big_dark_logo = models.FileField(upload_to='logos/', blank=True, null=True)
    big_light_logo = models.FileField(upload_to='logos/', blank=True, null=True)
    small_dark_logo = models.FileField(upload_to='logos/', blank=True, null=True)
    small_light_logo = models.FileField(upload_to='logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.website_name or "Unnamed Website"