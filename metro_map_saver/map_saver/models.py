# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from citysuggester.utils import suggest_city
from taggit.managers import TaggableManager

PUBLICLY_VISIBLE_TAGS = [
    'real',
    'speculative',
    'unknown',
]

class SavedMap(models.Model):

    """ Saves map data and its corresponding urlhash together so that maps can be easily shared
    """

    urlhash = models.CharField(max_length=64)
    mapdata = models.TextField()
    # gallery_visible: should this be shown in the default view of the Admin Gallery?
    gallery_visible = models.BooleanField(default=True, db_index=True)
    # publicly_visible: should this be shown in the publicly-visible gallery?
    #   (using this to improve speed and reduce query complexity)
    publicly_visible = models.BooleanField(default=False, db_index=True)
    name = models.CharField(max_length=255, blank=True, default='')
    thumbnail = models.TextField(blank=True, default='')
    stations = models.TextField(blank=True, default='')
    station_count = models.IntegerField(default=-1)
    created_at = models.DateField(auto_now_add=True)

    # Create a token that can be used for creators to be able to name their maps
    # but subsequent visitors to that map will not be able to rename it
    naming_token = models.CharField(max_length=64, blank=True, default='')

    tags = TaggableManager(blank=True)

    def suggest_city(self):
        return suggest_city(set(self.stations.lower().split(',')))

    def _station_count(self):
        if self.stations:
            return self.stations.count(',')
        else:
            return 0

    @property
    def _publicly_visible(self):
        return all([
            self.gallery_visible,
            self.name,
            self.thumbnail,
        ]) and set([tag.name for tag in self.tags.all()]).intersection(set(PUBLICLY_VISIBLE_TAGS))

    def __str__(self):
        return self.urlhash

    def save(self, *args, **kwargs):
        self.station_count = self._station_count()
        self.name = self.name.strip()
        self.thumbnail = self.thumbnail.strip()
        if self._publicly_visible:
            self.publicly_visible = True
        else:
            self.publicly_visible = False
        super().save(*args, **kwargs)

    class Meta:
        permissions = (
            ('hide_map', "Can set a map's gallery_visible to hidden"),
            ('name_map', "Can set a map's name"),
            ('tag_map', "Can change the tags associated with a map"),
            ('generate_thumbnail', "Can generate thumbnails for a map"),
            ('edit_publicly_visible', "Can edit a publicly visible map"),
        )
