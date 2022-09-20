# Generated by Django 4.0.6 on 2022-09-18 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_id', models.CharField(max_length=16, unique=True)),
                ('device_type', models.CharField(max_length=200)),
                ('device_availability', models.CharField(max_length=200)),
                ('device_description', models.TextField(blank=True, max_length=300)),
                ('added_by', models.CharField(max_length=200)),
                ('added_on', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'resource',
                'verbose_name_plural': 'resources',
            },
        ),
    ]