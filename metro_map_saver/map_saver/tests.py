# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from map_saver.models import SavedMap
from map_saver.validator import validate_metro_map

from django.core.management import call_command
from django.test import TestCase

class ValidateMapTestCase(TestCase):

    fixtures = ['untracked/backup-20180913-dates-backported.json']

    def test_fixtures_loaded(self):
        self.assertEqual(SavedMap.objects.count(), 2065)

    def test_validator(self):

        """ Ensure that all maps already saved will pass the validation
              as written in validate_metro_map()
            That way, I'll know any changes to validate_metro_map() have
              at least been tested on a large number of real, existing maps.
        """

        saved_maps = SavedMap.objects.all()
        for saved_map in saved_maps:
            saved_map = saved_map.mapdata.replace("u'", "'").replace("'", '"').strip('"').strip("'").replace('\\', '\\\\')
            validate_metro_map(saved_map)

    def test_invalid_toomanylines(self):

        """ Reject a map that has too many lines (Validation #04B: <= 100 lines)
        """
        pass
