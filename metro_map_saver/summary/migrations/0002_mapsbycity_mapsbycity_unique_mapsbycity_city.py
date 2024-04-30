# Generated by Django 5.0.1 on 2024-04-30 01:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map_saver', '0029_city_alter_savedmap_name_and_more'),
        ('summary', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MapsByCity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maps', models.IntegerField()),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='map_saver.city')),
                ('featured', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='map_saver.savedmap')),
            ],
        ),
        migrations.AddConstraint(
            model_name='mapsbycity',
            constraint=models.UniqueConstraint(fields=('city',), name='unique_mapsbycity_city'),
        ),
    ]
