from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from elearning.models import ELearning
from exam.models import Exam


@receiver(post_save, sender=Exam)
def create_elearning(sender, instance, created, **kwargs):
    if created and instance.exam_type == "elearning":
        ELearning.objects.create(id=instance.id, name=instance.name, author=instance.author, exam_type="elearning")