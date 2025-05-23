# Generated by Django 4.2 on 2024-08-08 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobsboard', '0024_remove_candidate_country_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employer',
            name='company_size',
            field=models.CharField(choices=[(5, 'Less Than 5'), (10, '6-10'), (20, '11-20'), (50, '21-50'), (100, '51-100'), (200, '101-200'), (500, '201-500'), (1000, 'More Than 500')], default=5, max_length=6),
        ),
    ]
