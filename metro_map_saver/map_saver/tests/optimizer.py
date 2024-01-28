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
        }

        for preopt, goal in expected.items():
            line = self.convert_to_xy_pairs(preopt)
            self.assertEqual(preopt.count(','), len(line))

            expected_length = goal.count(',')
            goal = self.convert_to_xy_pairs(goal)

            print(f'[DEBUG] line is: {line}')
            print(f'[DEBUG] goal is: {goal}')
            optimized = reduce_straight_line(line)
            print(f'[DEBUG] optimized is: {optimized}')

            self.assertEqual(optimized, goal)
            self.assertNotEqual(line, optimized)
