# import json

# from map_saver.models import SavedMap
# from map_saver.validator import validate_metro_map
from map_saver.mapdata_optimizer import (
    get_adjacent_point,
    is_adjacent,
    reduce_straight_line,
)

from django.test import TestCase
# from django.core.exceptions import ObjectDoesNotExist

class OptimizeMap(TestCase):

    """ Tests to optimize map data and especially collapse map data
        into the smallest non-lossy representation of x,y coordinate pairs
    """

    def convert_to_xy_pairs(self, linestring):

        """ Helper to convert a linestring of x,y pairs
            into a list of 2-tuples

            Ex: 1,1 1,5 -> [(1, 1), (1, 5)]
        """

        line = []
        for xy in linestring.split(' '):
            x, y = xy.split(',')
            line.append((int(x), int(y)))
        return line

    def test_reduce_straight_line(self):

        """ Confirm that we can reduce straight lines into
            very small representations of x,y coordinate pairs.

            So instead of having lots of coordinates in an SVG polyline like
                1,1 1,2 1,3 1,4 1,5, etc, we can instead write this as: 1,1 1,5
        """

        expected = {
            # Can reduce
            '1,1 1,2 1,3 1,4 1,5': '1,1 1,5',
            '1,1 2,1 3,1 4,1 5,1': '1,1 5,1',
            '1,1 2,2 3,3 4,4 5,5': '1,1 5,5',

            # Cannot reduce
            '1,1 1,2 10,30 10,31': '1,1 1,2 10,30 10,31',
        }

        for before, goal in expected.items():
            line = self.convert_to_xy_pairs(before)
            self.assertEqual(before.count(','), len(line))

            goal_line = self.convert_to_xy_pairs(goal)
            self.assertEqual(goal.count(','), len(goal_line))

            optimized = reduce_straight_line(line)

            self.assertEqual(optimized, goal_line)
            if before != goal:
                self.assertNotEqual(line, optimized)
                self.assertLess(len(optimized), len(line))

    def test_sort_points_by_color_v1(self):

        """ Confirm that given a JSON of mapdata,
                sort_points_by_color returns:
            * a dict of x,y points sorted by their color
            * a list of stations
            * the allowed map size

            This is more of a test for this function as compared to
                validation.test_convert_v1_to_v2,
                which does call sort_points_by_color
                but is more of an integration test.
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_sort_points_by_color_v2(self):

        """ As test_sort_points_by_color_v1, but for v2 data
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_get_connected_points(self):

        """ Confirm that get_connected_points returns
            a list of all points connected to x,y (inclusive)
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_is_adjacent(self):

        """ Confirm that is_adjacent()
            returns point2 if adjacent to point2
        """

        adjacent_points = [
            ((1,1), (0,0)),
            ((1,1), (1,0)),
            ((1,1), (2,0)),
            ((1,1), (0,1)),
            ((1,1), (2,1)),
            ((1,1), (0,2)),
            ((1,1), (1,2)),
            ((1,1), (2,2)),
        ]

        non_adjacent_points = [
            ((2,2), (0,0)),
            ((2,2), (1,0)),
            ((2,2), (2,0)),
            ((2,2), (3,0)),
            ((2,2), (4,0)),
            ((2,2), (4,1)),
            ((2,2), (4,2)),
            ((2,2), (4,3)),
            ((2,2), (4,4)),
            ((2,2), (3,4)),
            ((2,2), (2,4)),
            ((2,2), (1,4)),
            ((2,2), (0,4)),
            ((2,2), (0,3)),
            ((2,2), (0,2)),
            ((2,2), (0,1)),
        ]

        for p1, p2 in adjacent_points:
            self.assertEqual(p2, is_adjacent(p1, p2))

        for p1, p2 in non_adjacent_points:
            self.assertFalse(is_adjacent(p1, p2))

    def test_get_adjacent_point(self):

        """ Confirm that get_adjacent_point returns
            one adjacent point in order of preference:
                vertical, horizontal, diagonal
        """

        # Set examples up so the first point is fed into get_adjacent_point(),
        #   and the second point is what we expect to be returned.
        all_points = [
            # Has all points, so will prefer 1,2 (vertical)
            [(1,1), (1,2), (2,1), (2,2),],

            # Doesn't have vertical, so will prefer 12,11 (horizontal)
            [(11, 11), (12, 11), (12, 12),],

            # Doesn't have either, so will prefer diagonal
            [(21, 21), (22, 22),],

            # It's also fine with lower values, too. (vertical)
            [(32, 32), (31, 32), (32, 31), (31, 31),],
            [(42, 42), (41, 42), (41, 41),], # (horizontal)
            [(52, 52), (51, 51),], # (diagonal)
        ]

        for points in all_points:
            self.assertEqual(points[0], get_adjacent_point(points[1], points))

    def test_find_squares(self):

        """ Confirm that find_squares will return two lists of points:
            * the exterior border x,y points
            * the interior x,y points
            as long as all points are of the same color
            and are adjacent to one another in an N-sized square shape
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_get_line_direction(self):

        """ Confirm that metromap_utils.get_line_direction
            returns the direction the line is going in,
            which helps the placement/rotation of rectangle stations
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_get_connected_stations(self):

        """ Confirm that metromap_utils.get_connected_stations
            returns connected stations along a SINGLE direction,
            in the direction where there are the most stations,
            to facilitate drawing connected stations as a capsule or rect
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_station_marker(self):

        """ metromap_utils.station_marker is complex enough
            (esp with capsule stations and rectangles)
            and there's enough edge cases
            that it's worth confirming expected behaviors
        """

        self.assertFalse('TODO - Not yet implemented')
