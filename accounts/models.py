from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    isp = models.CharField(max_length=200, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    map_link = models.URLField(max_length=500, blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
