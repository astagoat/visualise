# Generated by Django 5.1.4 on 2025-01-10 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0002_fileupload'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
