# Generated by Django 4.0.6 on 2022-10-13 07:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0002_resourcetaken'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resourcetaken',
            name='return_date',
        ),
    ]
