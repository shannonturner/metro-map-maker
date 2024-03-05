from map_saver.templatetags.metromap_utils import (
    station_marker,
)

from django.test import TestCase

class StationMarkerTest(TestCase):

    """ Confirm the behavior of station markers
    """

    TODO = """
        if a station doesn't have a shape, use the map's default
        if xfer and line size >= 0.5, circle sm/md have a big white circle and small color circle
        elif xfer, circle sm/md have 1 color circle
        else, circle sm/md have a big color circle and small white circle
        circles lg: as wmata, but with color
        circles-thin: always b/w; xfer controls stroke width
        rectangles:
            if line size >= 0.5, drawn in b/w; otherwise color
            if line size >= 0.5, xfer controls stroke width
            if rounded, has radius of 0.125
        connected stations
        """

    def test_wmata(self):

        """ Confirm the styling of WMATA (Classic) stations
        """

        station = {'xy': (1,1), 'style': 'wmata', 'color': '#bd1038'}
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1"'), 2)
        self.assertEqual(marker.count('#fff'), 1)
        self.assertEqual(marker.count('#000'), 1)

        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1"'), 4)
        self.assertEqual(marker.count('#fff'), 2)
        self.assertEqual(marker.count('#000'), 2)
