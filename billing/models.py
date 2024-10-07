from django.db import models
from django.utils import timezone
from subscriptions.models import Package
from users.models import UserProfile

# Create your models here.
class BillingHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    package = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} - {self.description} - ${self.amount} (Package: {self.package})"
    
class Statement(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    order_id = models.CharField(max_length=100)
    details = models.CharField(max_length=255)
    credit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} - {self.order_id} - {self.details} - ${self.credit}"
