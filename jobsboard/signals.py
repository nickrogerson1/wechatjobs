from .models import *
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_delete, sender=Candidate)
def delete_cv_file(sender, instance, **kwargs):                          
    instance.cv.delete(False)

@receiver(post_save, sender=Candidate)
def save_user_cv(sender, instance, **kwargs):
    instance.cv.save()