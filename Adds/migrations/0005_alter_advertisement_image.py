# Generated by Django 5.1.7 on 2025-05-21 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Adds', '0004_alter_advertisement_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advertisement',
            name='image',
            field=models.ImageField(upload_to='advertisements/'),
        ),
    ]
