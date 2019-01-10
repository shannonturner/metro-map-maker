# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from map_saver.validator import html_dom_id_safe, convert_nonascii_to_ascii

class TravelSystem(models.Model):

    """ 
        A metro system of stations.

        More abstractly: 
            A way of getting around a place, with stops along the way

        Examples:
            Metro (DC)
            BART (SF)
            MUNI (SF)

        Used to suggest what city/system an unknown map is a map of.

        For example, if an unknown map has stations like 
            Fort Totten, Union Station, and Archives, it's probably DC's Metro
    """

    name = models.CharField(max_length=255, unique=True)
    stations = models.TextField() # all stations stored together, one per line

    def save(self, *args, **kwargs):

        """ Formats stations in the same manner as they are saved through the validator 
        """

        stations = self.stations.split('\n')
        for index, station in enumerate(stations):
            stations[index] = html_dom_id_safe(
                convert_nonascii_to_ascii(
                    stations[index].replace('/', ' - ').replace("'", '').replace('&', '').replace('`', '').replace('–', ' - ').replace(' ', '_')
                ).lower()
            ).strip()
        self.stations = '\n'.join(stations).strip()
        super(TravelSystem, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{0} ({1} stations)'.format(
            self.name, len(self.stations.split('\n'))
        )