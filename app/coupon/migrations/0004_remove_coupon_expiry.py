# Generated by Django 2.2.5 on 2020-12-30 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0003_auto_20201230_1228'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='expiry',
        ),
    ]