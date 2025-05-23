# Generated by Django 4.2 on 2024-08-23 15:10

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('jobsboard', '0037_promotedjob_times_promoted'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='time_updated',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now()),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='promotedjob',
            name='time_updated',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now()),
            preserve_default=False,
        ),
    ]
