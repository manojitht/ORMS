# Generated by Django 4.0.6 on 2022-11-07 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0004_resource_model_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]