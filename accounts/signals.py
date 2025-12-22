from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from .utils import get_client_ip_address, get_geo_data

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(user_logged_in)
def log_user_ip(sender, request, user, **kwargs):
    from .utils import update_user_ip_info
    update_user_ip_info(user, request)

