from django.db import models
import os
# Create your models here.



class UploadSlide(models.Model):
    """
    This model save the media images.
    """

    image = models.FileField(upload_to="media/")

    class Meta:
        db_table = "Uploading Slides"
        verbose_name = "Slide"
        verbose_name_plural = "Slides"

    def __str__(self):
        return self.image.name



class UploadImage(models.Model):
    """
    This model save the images in image folder.
    """

    image = models.ImageField(upload_to="static/img/")

