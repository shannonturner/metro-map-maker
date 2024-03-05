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
        circles-thin: always b/w; xfer controls stroke width
        rectangles:
            if line size >= 0.5, drawn in b/w; otherwise color
            if line size >= 0.5, xfer controls stroke width
            if rounded, has radius of 0.125
        connected stations
        """

    def test_wmata(self, line_color='bd1038', station_color='#000', style='wmata'):

        """ Confirm the styling of WMATA (Classic) stations
        """

        station = {'xy': (1,1), 'style': style, 'color': line_color}
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1"'), 2)
        self.assertEqual(marker.count('#fff'), 1)
        self.assertEqual(marker.count(station_color), 1)

        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1"'), 4)
        self.assertEqual(marker.count('#fff'), 2)
        self.assertEqual(marker.count(station_color), 2)

    def test_circles_lg(self):

        """ circles-lg is really just WMATA styling but
            with the line color instead
        """

        self.test_wmata(line_color='bd1038', station_color='#bd1038', style='circles-lg')
