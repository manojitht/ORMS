# Generated by Django 4.0.6 on 2022-11-07 10:58

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0003_alter_resourcetaken_resource_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='model_name',
            field=models.CharField(default=django.utils.timezone.now, max_length=200),
            preserve_default=False,
        ),
    ]