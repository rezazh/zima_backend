# Generated by Django 5.1.5 on 2025-06-09 13:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_customuser_is_online'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='is_online',
        ),
    ]
