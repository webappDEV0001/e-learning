from django.db import models
import os
# Create your models here.



class UploadSlide(models.Model):
    """
    This model save the media images.
    """

    image = models.ImageField(upload_to="media/")

    class Meta:
        db_table = "Uploading Slides"



class UploadImage(models.Model):
    """
    This model save the images in image folder.
    """

    image = models.ImageField(upload_to="static/img/")

