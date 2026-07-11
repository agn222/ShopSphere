from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, Wishlist


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_related_data(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        Wishlist.objects.get_or_create(user=instance)