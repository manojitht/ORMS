# Generated by Django 4.0.6 on 2023-02-05 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0009_otheraccessories'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcetaken',
            name='manager_peoplesoft_id',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
