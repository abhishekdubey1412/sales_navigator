# Generated by Django 5.1 on 2024-10-08 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ContactUs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('subject', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='WebsiteDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('website_name', models.CharField(blank=True, max_length=50, null=True)),
                ('favicon', models.FileField(blank=True, null=True, upload_to='logos/')),
                ('big_dark_logo', models.FileField(blank=True, null=True, upload_to='logos/')),
                ('big_light_logo', models.FileField(blank=True, null=True, upload_to='logos/')),
                ('small_dark_logo', models.FileField(blank=True, null=True, upload_to='logos/')),
                ('small_light_logo', models.FileField(blank=True, null=True, upload_to='logos/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
