# Generated by Django 2.2.5 on 2019-11-17 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0005_auto_20191117_0402'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='time_limit',
            field=models.IntegerField(default=30),
        ),
    ]