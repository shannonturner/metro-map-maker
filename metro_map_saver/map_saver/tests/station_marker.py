from map_saver.templatetags.metromap_utils import (
    station_marker,
)

from django.test import TestCase

class StationMarkerTest(TestCase):

    """ Confirm the behavior of station markers
    """

    TODO = """
        rectangles:
            if line size >= 0.5, drawn in b/w; otherwise color
            if line size >= 0.5, xfer controls stroke width
            if rounded, has radius of 0.125
        """

    points_by_color = {
        # A set of horizontal, vertical, diagonal-se, diagonal-ne points, and some singletons
        'bd1038': {
            'xy': [
                (1,1), (2,1), (3,1), (4,1), (5,1),
                (11,1), (11,2), (11,3), (11,4), (11,5),
                (21,1), (22,2), (23,3), (24,4), (25,5),
                (31,5), (32,4), (33,3), (34,2), (35,1),
                (40,0), (50,0), (60,0), (70,0), (80,0),
            ],
        },
        '00b251': {
            'xy': [
                (1,2), (2,2), (3,2), (4,2), (5,2),
                (12,1), (12,2), (12,3), (12,4), (12,5),
                (22,1), (23,2), (24,3), (25,4), (26,5),
                (32,5), (33,4), (34,3), (35,2), (36,1),
                (40,10), (50,10), (60,10), (70,10), (80,10),
            ],
        },
        '0896d7': {
            'xy': [
                (1,3), (2,3), (3,3), (4,3), (5,3),
                (13,1), (13,2), (13,3), (13,4), (13,5),
                (23,1), (24,2), (25,3), (26,4), (27,5),
                (33,5), (34,4), (35,3), (36,2), (37,1),
                (40,20), (50,20), (60,20), (70,20), (80,20),
            ],
        },
    }

    stations = [
        # Vertical Connected
        {'xy': (1,1), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'connected'},
        {'xy': (1,2), 'color': '00b251', 'style': 'rect-round', 'expected': 'interior'},
        {'xy': (1,3), 'color': '0896d7', 'style': 'rect-round', 'expected': 'interior'},

        # Horizontal Connected
        {'xy': (11,2), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'connected'},
        {'xy': (12,2), 'color': '00b251', 'style': 'rect-round', 'expected': 'interior'},
        {'xy': (13,2), 'color': '0896d7', 'style': 'rect-round', 'expected': 'interior'},

        # Diagonal NE Connected
        {'xy': (31,5), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'connected'},
        {'xy': (32,4), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'interior'},
        {'xy': (33,3), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'interior'},

        # Diagonal SE Connected
        {'xy': (23,1), 'color': '0896d7', 'style': 'rect-round', 'expected': 'connected'},
        {'xy': (24,2), 'color': '0896d7', 'style': 'rect-round', 'expected': 'interior'},
        {'xy': (25,3), 'color': '0896d7', 'style': 'rect-round', 'expected': 'interior'},

        # Singletons
        {'xy': (80,0), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'singleton'},
        {'xy': (80,10), 'color': '00b251', 'style': 'rect-round', 'expected': 'singleton'},
        {'xy': (80,20), 'color': '0896d7', 'style': 'rect-round', 'expected': 'singleton'},
    ]



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

    def test_circles_md(self):

        """ Confirm that circles-md stations have three options:
            transfer & line_size >= 0.5
            transfer
            non-transfer
        """

        station = {'xy': (1,1), 'style': 'circles-md', 'color': 'bd1038'}
        # Non-transfer
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.5" fill="#bd1038"'), 1)
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.25" fill="#fff"'), 1)

        # Transfer (thin line)
        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.5" fill="#bd1038"'), 1)

        # Transfer (thick line)
        marker = station_marker(station, 'wmata', 0.5, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.5" fill="#fff"'), 1)
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.25" fill="#bd1038"'), 1)

    def test_circles_sm(self):

        """ Confirm that circles-sm stations have three options:
            transfer & line_size >= 0.5
            transfer
            non-transfer
        """

        station = {'xy': (1,1), 'style': 'circles-sm', 'color': 'bd1038'}
        # Non-transfer
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.4" fill="#bd1038"'), 1)
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.2" fill="#fff"'), 1)

        # Transfer (thin line)
        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.4" fill="#bd1038"'), 1)

        # Transfer (thick line)
        marker = station_marker(station, 'wmata', 0.5, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.4" fill="#fff"'), 1)
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.2" fill="#bd1038"'), 1)

    def test_default_shape(self):

        """ Confirm that if station does not have a style (shape),
                the default will be used.
        """

        station = {'xy': (1,1), 'color': 'bd1038'}
        marker = station_marker(station, 'circles-sm', 0.125, {}, {})
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.4" fill="#bd1038"'), 1)
        self.assertEqual(marker.count('<circle cx="1" cy="1" r="0.2" fill="#fff"'), 1)

    def test_circles_thin(self):

        """ Confirm that circles-thin is drawn as a b/w circle,
                with thicker stroke for transfer stations;
                and with connecting stations when appropriate.
        """

        for station in self.stations:
            x = station['xy'][0]
            y = station['xy'][1]

            station['style'] = 'circles-thin'

            if station['expected'] == 'connected':
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertEqual(marker.count('<rect '), 1)
                self.assertEqual(marker.count('<circle '), 0)
            elif station['expected'] == 'interior':
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertFalse(marker)
            elif station['expected'] == 'singleton':
                station['transfer'] = 0
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertEqual(marker, f'<circle cx="{x}" cy="{y}" r="0.5" fill="#fff" stroke="#000" stroke-width="0.1"/>')

                station['transfer'] = 1
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertEqual(marker, f'<circle cx="{x}" cy="{y}" r="0.5" fill="#fff" stroke="#000" stroke-width="0.2"/>')

    def test_rectangles_connected(self):

        """ Confirm behavior of rectangle connected stations;
            will test rectangle singletons separately
        """

        for station in self.stations:
            x = station['xy'][0]
            y = station['xy'][1]

            station['style'] = 'rect'

            if station['expected'] == 'connected':
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertEqual(marker.count('<rect '), 1)
                self.assertTrue('width="3' in marker or 'height="3' in marker)
                self.assertNotIn('rx=', marker)
            elif station['expected'] == 'interior':
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertFalse(marker)

    def test_rounded_rectangles_connected(self):

        """ Confirm behavior of rounded rectangle connected stations;
            will test rounded rectangle singletons separately
        """

        for station in self.stations:
            x = station['xy'][0]
            y = station['xy'][1]

            station['style'] = 'rect-round'

            if station['expected'] == 'connected':
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertEqual(marker.count('<rect '), 1)
                self.assertTrue('width="3' in marker or 'height="3' in marker)
                self.assertIn('rx=', marker)
            elif station['expected'] == 'interior':
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertFalse(marker)
