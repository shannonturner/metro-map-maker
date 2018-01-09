# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class SavedMap(models.Model):

    """ Saves map data and its corresponding urlhash together so that maps can be easily shared
    """

    urlhash = models.CharField(max_length=64)
    mapdata = models.TextField()
    gallery_visible = models.BooleanField(default=True)

    def __unicode__(self):
        return self.urlhash
