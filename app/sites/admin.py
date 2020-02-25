from django.contrib import admin
from sites.models import UploadSlide
# Register your models here.
from sites.forms import FormUploadSlide


@admin.register(UploadSlide)
class UploadSlide(admin.ModelAdmin):
    form = FormUploadSlide