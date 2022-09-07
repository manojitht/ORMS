# Generated by Django 4.0.6 on 2022-09-05 03:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('peoplesoft_id', models.CharField(max_length=8, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=100, unique=True)),
                ('department', models.CharField(max_length=200)),
                ('team', models.CharField(max_length=200)),
                ('role', models.CharField(max_length=100)),
                ('date_joined', models.DateTimeField(default=datetime.datetime.now)),
                ('last_login', models.DateTimeField(auto_now_add=True)),
                ('is_superadmin', models.BooleanField(default=False, verbose_name='Is Superadmin')),
                ('is_it_admin', models.BooleanField(default=False, verbose_name='Is IT Admin')),
                ('is_manager', models.BooleanField(default=False, verbose_name='Is Manager')),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
