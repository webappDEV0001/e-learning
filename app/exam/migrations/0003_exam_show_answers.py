# Generated by Django 2.2.5 on 2019-11-16 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0002_exam_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='show_answers',
            field=models.BooleanField(default=True),
        ),
    ]