# Generated by Django 5.0.1 on 2024-06-18 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0031_savedmap_map_saver_s_suggest_e73177_idx'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='city',
            index=models.Index(fields=['name'], name='map_saver_c_name_f3a223_idx'),
        ),
    ]
