from django import forms
import zipfile
from zipfile import ZipFile
from sites.models import UploadSlide
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from wand.image import Image as wi
from pdf2image import convert_from_path, convert_from_bytes
import tempfile
import os
import glob
from PIL import Image as PImage
from PIL import Image
import cv2
from config.common import *
from django.core.files import File

class FormUploadSlide(forms.ModelForm):
    class Meta:
        model = UploadSlide
        fields = ("image",)


    def clean_image(self):
        file = self.cleaned_data.get("image")

        # check for zip folder
        if not ".zip" in str(file):
            raise forms.ValidationError("Please enter a zip file")

        zip_list = []
        with ZipFile(file, 'r') as zip:
            for info in zip.infolist():
                zip_list.append(info.filename)
            result = [ele for ele in zip_list if (".pdf" in str(ele))]  # check if file contain pptx file
            print(result)
            if bool(result) is True:
                save_path = os.path.join(MEDIA_ROOT, "pdf_images/")
                for file in result:
                    myfile = zip.read(file)
                    i = 1
                    with tempfile.TemporaryDirectory() as path:
                        images_from_path = convert_from_bytes(myfile, output_folder=path)
                        for page in images_from_path:
                            page.save(save_path+str(i)+".jpg", 'JPEG')  #save image in folder 'pdf_images' temporary
                            i += 1

                imagesList = glob.glob(save_path+"*.jpg")
                for image in imagesList:
                    new_path = os.path.abspath(image)
                    new_path = new_path.split("media/")[1]
                    UploadSlide.objects.get_or_create(image=new_path)

            else:
                raise forms.ValidationError("This folder not contain pdf file Please try another.")

        return file

