from django.db import models
import os
# Create your models here.

from django.core.files.storage import FileSystemStorage

from config.common import STATICFILES_DIRS

PRIVATE_DIR = os.path.join(STATICFILES_DIRS[0], 'img')
fs = FileSystemStorage(location=PRIVATE_DIR)


class UploadMedia(models.Model):
    """
    This model save the media images.
    """

    image = models.ImageField(upload_to="media/")


class UploadImage(models.Model):
    """
    This model save the images in image folder.
    """

    image = models.ImageField(upload_to="static/img/", storage=fs)

