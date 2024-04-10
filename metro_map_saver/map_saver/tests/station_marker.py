from map_saver.templatetags.metromap_utils import (
    get_station_styles_in_use,
    station_marker,
)
from map_saver.validator import ALLOWED_LINE_WIDTHS

from django.test import TestCase

class StationMarkerTest(TestCase):

    """ Confirm the behavior of station markers
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

        # Singletons in point and station
        {'xy': (80,0), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'singleton'},
        {'xy': (80,10), 'color': '00b251', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'singleton'},
        {'xy': (80,20), 'color': '0896d7', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'singleton'},

        # Singleton stations on a line
        {'xy': (3,1), 'color': 'bd1038', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'horizontal'},
        {'xy': (13,4), 'color': '0896d7', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'vertical'},
        {'xy': (26,5), 'color': '00b251', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'diagonal-se'},
        {'xy': (37,1), 'color': '0896d7', 'style': 'rect-round', 'expected': 'singleton', 'line_direction': 'diagonal-ne'},
    ]

    def test_wmata(self, line_color='bd1038', station_color='#000', style='wmata', ref='wm'):

        """ Confirm the styling of WMATA (Classic) stations
        """

        expected_circles = 6
        expected_colors = 3

        station = {'xy': (1,1), 'style': style, 'color': line_color}
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker, f'<use x="1" y="1" href="#{ref}"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .5)
        self.assertEqual(svg_defs.count('<circle'), expected_circles)
        self.assertEqual(svg_defs.count(f'fill="{station_color}"'), expected_colors)
        self.assertEqual(svg_defs.count('fill="#fff"'), expected_colors)
        self.assertIn(f'<g id="{ref}">', svg_defs)

        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker, f'<use x="1" y="1" href="#{ref}-xf"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .5)
        self.assertEqual(svg_defs.count('<circle'), expected_circles)
        self.assertEqual(svg_defs.count(f'fill="{station_color}"'), expected_colors)
        self.assertEqual(svg_defs.count('fill="#fff"'), expected_colors)
        self.assertIn(f'<g id="{ref}-xf">', svg_defs)

    def test_circles_lg(self):

        """ circles-lg is really just WMATA styling but
            with the line color instead
        """

        expected_circles = 2
        expected_colors = 1
        line_color = 'bd1038'
        ref = 'clg'

        station = {'xy': (1,1), 'style': 'circles-lg', 'color': line_color}
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker, f'<use x="1" y="1" href="#{ref}-{line_color}"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .5)
        self.assertEqual(svg_defs.count('<circle'), expected_circles)
        self.assertEqual(svg_defs.count(f'fill="#{line_color}"'), expected_colors)
        self.assertEqual(svg_defs.count('fill="#fff"'), expected_colors)
        self.assertIn(f'<g id="{ref}-{line_color}">', svg_defs)

        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 1, {}, {})
        self.assertEqual(marker, f'<use x="1" y="1" href="#{ref}-xf-{line_color}"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .5)
        self.assertEqual(svg_defs.count('<circle'), expected_circles * 2)
        self.assertEqual(svg_defs.count(f'fill="#{line_color}"'), expected_colors * 2)
        self.assertEqual(svg_defs.count('fill="#fff"'), expected_colors * 2)
        self.assertIn(f'<g id="{ref}-xf-{line_color}">', svg_defs)

    def test_circles_md(self):

        """ Confirm that circles-md stations have three options:
            transfer & line_size >= 0.5
            transfer
            non-transfer
        """

        station = {'xy': (1,1), 'style': 'circles-md', 'color': 'bd1038'}
        # Non-transfer
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#cmd-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .25)
        self.assertEqual(svg_defs.count('<circle r="0.5" fill="#bd1038"'), 1)
        self.assertEqual(svg_defs.count('<circle r="0.25" fill="#fff"'), 1)

        # Transfer (thin line)
        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#cmd-xf-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .25)
        self.assertEqual(svg_defs.count('<circle r="0.5" fill="#bd1038"'), 1)

        # Transfer (thick line)
        marker = station_marker(station, 'wmata', 0.5, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#cmd-xf-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .5)
        self.assertEqual(svg_defs.count('<circle r="0.5" fill="#fff"'), 1)
        self.assertEqual(svg_defs.count('<circle r="0.25" fill="#bd1038"'), 1)

    def test_circles_sm(self):

        """ Confirm that circles-sm stations have three options:
            transfer & line_size >= 0.5
            transfer
            non-transfer
        """

        station = {'xy': (1,1), 'style': 'circles-sm', 'color': 'bd1038'}
        # Non-transfer
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#csm-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .25)
        self.assertEqual(svg_defs.count('<circle r="0.4" fill="#bd1038"'), 1)
        self.assertEqual(svg_defs.count('<circle r="0.2" fill="#fff"'), 1)

        # Transfer (thin line)
        station['transfer'] = 1
        marker = station_marker(station, 'wmata', 0.25, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#csm-xf-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .25)
        self.assertEqual(svg_defs.count('<circle r="0.4" fill="#bd1038"'), 1)

        # Transfer (thick line)
        marker = station_marker(station, 'wmata', 0.5, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#csm-xf-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-thin', .5)
        self.assertEqual(svg_defs.count('<circle r="0.4" fill="#fff"'), 1)
        self.assertEqual(svg_defs.count('<circle r="0.2" fill="#bd1038"'), 1)

    def test_default_shape(self):

        """ Confirm that if station does not have a style (shape),
                the default will be used.
        """

        station = {'xy': (1,1), 'color': 'bd1038'}
        marker = station_marker(station, 'circles-sm', 0.125, {}, {})
        self.assertEqual(marker, '<use x="1" y="1" href="#csm-bd1038"/>')
        svg_defs = get_station_styles_in_use([station], 'circles-sm', .125)
        self.assertEqual(svg_defs.count('<circle r="0.4" fill="#bd1038"'), 1)
        self.assertEqual(svg_defs.count('<circle r="0.2" fill="#fff"'), 1)

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
                self.assertEqual(marker, f'<use x="{x}" y="{y}" href="#ct"/>')

                svg_defs = get_station_styles_in_use([station], 'wmata', .5)
                self.assertEqual(svg_defs.count('<circle r="0.5" fill="#fff" stroke="#000" stroke-width="0.1"/>'), 1)
                self.assertIn(f'<g id="ct">', svg_defs)

                station['transfer'] = 1
                marker = station_marker(station, 'circles-thin', 0.125, self.points_by_color, self.stations)
                self.assertEqual(marker, f'<use x="{x}" y="{y}" href="#ct-xf"/>')

                svg_defs = get_station_styles_in_use([station], 'wmata', .5)
                self.assertEqual(svg_defs.count('<circle r="0.5" fill="#fff" stroke="#000" stroke-width="0.2"/>'), 1)
                self.assertIn(f'<g id="ct-xf">', svg_defs)

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


    def test_rectangles_not_connected(self, rounded=False):

        """ Confirm that non-connected rectangle station markers
            are drawn as expected
        """

        for line_width in ALLOWED_LINE_WIDTHS:
            # Singletons only
            for station in self.stations[-7:]:
                marker = station_marker(station, 'wmata', line_width, self.points_by_color, self.stations)
                self.assertEqual(marker.count('<rect '), 1)
                self.assertTrue('width="1"' in marker or 'width="0.5"' in marker)
                self.assertTrue('height="1"' in marker or 'height="0.5"' in marker)

                if rounded:
                    if line_width >= 0.5 or station['line_direction'] == 'singleton':
                        self.assertIn('fill="#fff"', marker)
                        self.assertIn('stroke="#000"', marker)
                    else:
                        self.assertIn(f'fill="#{station["color"]}"', marker)
                else:
                    # If line size >= 0.5, drawn in b/w; otherwise color
                    if station['line_direction'] == 'singleton':
                        self.assertIn(f'fill="#{station["color"]}"', marker)
                    elif line_width >= 0.5:
                        self.assertIn('fill="#fff"', marker)
                        self.assertIn('stroke="#000"', marker)
                    else:
                        self.assertIn(f'fill="#{station["color"]}"', marker)

                # If rounded, has radius of 0.125
                if rounded:
                    self.assertIn('rx="0.125"', marker)
                else:
                    self.assertNotIn('rx="0.125"', marker)

                if 'diagonal' in station['line_direction']:
                    self.assertIn('transform="rotate', marker)
                else:
                    self.assertNotIn('transform="rotate', marker)

    def test_rounded_rectangles_not_connected(self):
        self.test_rectangles_not_connected(rounded=True)
