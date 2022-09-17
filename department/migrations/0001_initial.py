# Generated by Django 4.0.6 on 2022-09-17 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department_name', models.CharField(max_length=150, unique=True)),
                ('department_head', models.CharField(max_length=150)),
                ('department_description', models.TextField(blank=True, max_length=255)),
                ('created_by', models.CharField(max_length=150)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'department',
                'verbose_name_plural': 'departments',
            },
        ),
    ]
