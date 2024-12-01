# Generated by Django 5.1.2 on 2024-11-28 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0032_city_map_saver_c_name_f3a223_idx'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedmap',
            name='browse_visible',
            field=models.BooleanField(default=True, help_text='Uncheck this to disable a map from being able to be browsed in the maps by date and similar views, though it is still accessible by direct link.'),
        ),
        migrations.AlterField(
            model_name='savedmap',
            name='gallery_visible',
            field=models.BooleanField(default=True, help_text='Should this be shown in the default view of the Admin Gallery?'),
        ),
        migrations.AddIndex(
            model_name='savedmap',
            index=models.Index(fields=['browse_visible'], name='map_saver_s_browse__add01f_idx'),
        ),
    ]