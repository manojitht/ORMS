# Generated by Django 4.0.6 on 2022-11-07 09:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resourcetaken',
            name='resource_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resource.category'),
        ),
    ]
