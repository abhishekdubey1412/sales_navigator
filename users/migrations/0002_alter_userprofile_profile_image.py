# Generated by Django 5.1 on 2024-10-11 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_image',
            field=models.FileField(blank=True, default='avatars/default_image.jpg', null=True, upload_to='avatars/'),
        ),
    ]
