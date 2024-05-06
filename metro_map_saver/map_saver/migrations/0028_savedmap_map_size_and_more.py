# Generated by Django 5.0.1 on 2024-04-24 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0027_identifymap'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedmap',
            name='map_size',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddIndex(
            model_name='savedmap',
            index=models.Index(fields=['name'], name='map_saver_s_name_dd6eb8_idx'),
        ),
    ]