# Generated by Django 2.1.11 on 2020-11-22 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0015_savedmap_suggested_city_overlap'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savedmap',
            name='urlhash',
            field=models.CharField(db_index=True, max_length=8),
        ),
    ]
