from django.db.models.signals import post_save
from django.dispatch import receiver

from sites.models import UploadSlide


@receiver(post_save, sender=UploadSlide)
def create_slide(sender, instance, created,  **kwargs):
    if created and ".pdf" in instance.image.name:
        instance.delete()
