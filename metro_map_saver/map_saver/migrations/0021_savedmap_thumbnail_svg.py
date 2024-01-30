# Generated by Django 5.0.1 on 2024-01-26 03:05

import map_saver.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0020_savedmap_map_saver_s_station_087683_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedmap',
            name='thumbnail_svg',
            field=models.FileField(null=True, upload_to=map_saver.models.get_thumbnail_filepath),
        ),
    ]