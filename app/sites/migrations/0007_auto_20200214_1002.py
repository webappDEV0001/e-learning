# Generated by Django 2.2.5 on 2020-02-14 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Uploading', '0006_auto_20200212_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadslide',
            name='image',
            field=models.FileField(upload_to='media/'),
        ),
    ]