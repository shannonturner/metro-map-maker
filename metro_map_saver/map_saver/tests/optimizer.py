# import json

# from map_saver.models import SavedMap
# from map_saver.validator import validate_metro_map
from map_saver.mapdata_optimizer import reduce_straight_line

from django.test import TestCase
# from django.core.exceptions import ObjectDoesNotExist

class OptimizeMap(TestCase):

    """ Tests to optimize map data and especially collapse map data
        into the smallest non-lossy representation of x,y coordinate pairs
    """

    TODO = """
    sort_points_by_color returns points_by_color, stations, map_size from v1 map_data
        sort_points_by_color isn't pointless for v2 (it's used to generate images, for one), but can probably be streamlined as compared to v1.
        regardless, both implementations will need testing
    get_connected_points should return recursively-generated list of 2-tuples with all connected points for x,y, self-inclusive
    is_adjacent should return point2 if point2 is adjacent to point1, otherwise None
    get_adjacent_point should return horizontal, vertical, or diagonal (in pref order)
    find_squares should find squares of contiguous colors from points_this_color, of a given width, returning lists: squares_ext, squares_int
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
