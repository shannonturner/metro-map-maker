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

    tags = TaggableManager(blank=True)

    def suggest_city(self):
        return suggest_city(set(self.stations.split(',')))

    def __unicode__(self):
        return self.urlhash
