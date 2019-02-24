# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from citysuggester.utils import suggest_city
from taggit.managers import TaggableManager

class SavedMap(models.Model):

    """ Saves map data and its corresponding urlhash together so that maps can be easily shared
    """

    urlhash = models.CharField(max_length=64)
    mapdata = models.TextField()
    gallery_visible = models.BooleanField(default=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, default='')
    thumbnail = models.TextField(blank=True, default='')
    stations = models.TextField(blank=True, default='')
    created_at = models.DateField(auto_now_add=True)

    # Create a token that can be used for creators to be able to name their maps
    # but subsequent visitors to that map will not be able to rename it
    naming_token = models.CharField(max_length=64, blank=True, default='')

    tags = TaggableManager(blank=True)

    def suggest_city(self):
        return suggest_city(set(self.stations.lower().split(',')))

    def station_count(self):
        return len(self.stations.strip(',').split(','))

    def __str__(self):
        return self.urlhash

    class Meta:
        permissions = (
            ('hide_map', "Can set a map's gallery_visible to hidden"),
            ('name_map', "Can set a map's name"),
            ('tag_map', "Can change the tags associated with a map"),
            ('generate_thumbnail', "Can generate thumbnails for a map"),
        )
