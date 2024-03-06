from map_saver.mapdata_optimizer import (
    find_squares,
    get_adjacent_point,
    get_connected_points,
    is_adjacent,
    reduce_straight_line,
    sort_points_by_color,
)

from map_saver.templatetags.metromap_utils import (
    get_line_direction,
    get_connected_stations,
)

from django.test import TestCase

class OptimizeMapTest(TestCase):

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

        # mUCL18da
        mapdata = '{"1":{"1":{"line":"00b251"},"2":{"line":"00b251"},"3":{"line":"00b251"},"4":{"line":"00b251"},"5":{"line":"00b251"},"6":{"line":"00b251"},"7":{"line":"00b251"},"8":{"line":"00b251","station":{"name":"Green SW","orientation":45}}},"2":{"1":{"line":"00b251"},"2":{"line":"0896d7"},"3":{"line":"0896d7"},"4":{"line":"0896d7"},"5":{"line":"0896d7"},"6":{"line":"0896d7"},"7":{"line":"0896d7"},"8":{"line":"00b251"}},"3":{"1":{"line":"00b251"},"2":{"line":"0896d7"},"3":{"line":"bd1038","station":{"name":"Red NW","orientation":-45,"style":"rect","transfer":1}},"4":{"line":"0896d7"},"5":{"line":"0896d7"},"6":{"line":"bd1038"},"7":{"line":"0896d7"},"8":{"line":"00b251"}},"4":{"1":{"line":"00b251"},"2":{"line":"0896d7"},"3":{"line":"0896d7"},"4":{"line":"bd1038"},"5":{"line":"bd1038"},"6":{"line":"0896d7"},"7":{"line":"0896d7"},"8":{"line":"00b251"}},"5":{"1":{"line":"00b251"},"2":{"line":"0896d7"},"3":{"line":"0896d7"},"4":{"line":"bd1038"},"5":{"line":"bd1038"},"6":{"line":"0896d7"},"7":{"line":"0896d7"},"8":{"line":"00b251"}},"6":{"1":{"line":"00b251"},"2":{"line":"0896d7"},"3":{"line":"bd1038"},"4":{"line":"0896d7"},"5":{"line":"0896d7"},"6":{"line":"bd1038"},"7":{"line":"0896d7"},"8":{"line":"00b251"}},"7":{"1":{"line":"00b251"},"2":{"line":"0896d7","station":{"name":"Blue NE","style":"circles-lg"}},"3":{"line":"0896d7"},"4":{"line":"0896d7"},"5":{"line":"0896d7"},"6":{"line":"0896d7"},"7":{"line":"0896d7"},"8":{"line":"00b251"}},"8":{"1":{"line":"00b251"},"2":{"line":"00b251"},"3":{"line":"00b251"},"4":{"line":"00b251"},"5":{"line":"00b251"},"6":{"line":"00b251"},"7":{"line":"00b251"},"8":{"line":"00b251"}},"global":{"lines":{"0896d7":{"displayName":"Blue Line"},"00b251":{"displayName":"Green Line"},"bd1038":{"displayName":"Red Line"}},"map_size":160,"style":{"mapStationStyle":"circles-thin","mapLineWidth":0.125}},"points_by_color":{},"stations":{}}'

        points_by_color, stations, map_size = sort_points_by_color(mapdata, map_type='classic', data_version=1)

        self.assertEqual(map_size, 80)
        self.assertEqual(len(stations), 3)
        self.assertEqual(
            stations,
            [
                {'name': 'Green SW', 'orientation': 45, 'xy': (1,8), 'color': '00b251'},
                {'name': 'Red NW', 'orientation': -45, 'xy': (3,3), 'color': 'bd1038', 'transfer': 1, 'style': 'rect'},
                {'name': 'Blue NE', 'orientation': 0, 'xy': (7,2), 'color': '0896d7', 'style': 'circles-lg'},
            ]
        )
        self.assertEqual(len(points_by_color['bd1038']['xy']), 8)
        self.assertEqual(len(points_by_color['00b251']['xy']), 28)
        self.assertEqual(len(points_by_color['0896d7']['xy']), 28)

        # Confirm a handful of the expected points exist
        expected = {
            'bd1038': [(3,3), (4,4), (5,5), (6,6), (6,3), (3,6)],
            '00b251': [(1,1), (1,8), (8,8), (8,1), (8,5), (1,4)],
            '0896d7': [(2,2), (7,2), (7,7), (2,7), (3,5), (6,4)],
        }

        for color in expected:
            for point in expected[color]:
                self.assertIn(point, points_by_color[color]['xy'])

    def test_sort_points_by_color_v2(self):

        """ As test_sort_points_by_color_v1, but for v2 data
        """

        self.assertFalse('TODO - Not yet implemented')

    def test_get_connected_points(self):

        """ Confirm that get_connected_points returns
            a list of all points connected to x,y (inclusive)
        """

        connected = [
            (1,1), (1,2), (1,3), (1,4), # S
            (2,5), (3,6), (4,6), (5,6), # SE, E
            (6,5), (7,4), (6,3), (7,2), # NE, NW
            (8,1), (7,0), (6,0), (5,1), # NE, NW, W, SW
            (4,2), (3,2), (3,1), (3,0), # SW, W, N
        ]

        unconnected = [
            (10,10), (12,12), (4,4),
        ]

        for xy in connected:
            # Doesn't matter which point you start from!
            connected_points = get_connected_points(xy[0], xy[1], connected + unconnected)
            self.assertEqual(sorted(connected), sorted(connected_points))

        for point in connected_points:
            self.assertNotIn(point, unconnected)

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

        # First, make the square
        points_this_color = {'xy': [], 'x': [], 'y': []}
        for x in range(1, 6):
            for y in range(1, 6):
                points_this_color['x'].append(x) # Yes, this is repetitive -- that's a feature
                points_this_color['y'].append(y)
                points_this_color['xy'].append((x, y))

        # In a 5x5 square, there are 16 exterior points and 9 interior points
        exterior, interior = find_squares(points_this_color, width=5)
        self.assertEqual(len(exterior[0]), 16)
        self.assertEqual(len(interior[0]), 9)

        for point in exterior[0]:
            # Exterior points will all have either an x of (1,5)
            #   or a y of (1,5);
            # Interior points will have none of these
            self.assertTrue(point[0] in (1,5) or point[1] in (1,5))

        for point in interior[0]:
            self.assertFalse(point[0] in (1,5) or point[1] in (1,5))
            self.assertTrue(point[0] in (2,3,4) and point[1] in (2,3,4))

        # This can also be used to find squares of smaller (or larger) sizes
        exterior, interior = find_squares(points_this_color, width=4)
        self.assertEqual(len(exterior[0]), 12)
        self.assertEqual(len(interior[0]), 4)

        for point in exterior[0]:
            self.assertTrue(point[0] in (1, 4) or point[1] in (1,4))

        for point in interior[0]:
            self.assertFalse(point[0] in (1,4) or point[1] in (1,4))
            self.assertTrue(point[0] in (2,3) and point[1] in (2,3))

        # Smallest square is 3x3
        exterior, interior = find_squares(points_this_color, width=3)
        self.assertEqual(len(exterior[0]), 8)
        self.assertEqual(len(interior[0]), 1)

        for point in exterior[0]:
            self.assertTrue(point[0] in (1, 3) or point[1] in (1,3))

        for point in interior[0]:
            self.assertFalse(point[0] in (1,3) or point[1] in (1,3))
            self.assertTrue(point[0] in (2,) and point[1] in (2,))

        # Removing even one point means that there's no square.
        points_this_color['xy'].remove((3,3))
        exterior, interior = find_squares(points_this_color, width=5)
        self.assertFalse(exterior)
        self.assertFalse(interior)

    def test_get_line_direction(self):

        """ Confirm that metromap_utils.get_line_direction
            returns the direction the line is going in,
            which helps the placement/rotation of rectangle stations
        """

        horizontal = [(1,1), (2,1), (3,1), (4,1)]
        vertical = [(1,3), (1,4), (1,5), (1,6)]
        diagonal_se = [(4,4), (5,5), (6,6), (7,7)]
        diagonal_ne = [(10,10), (11,9), (12,8), (13,7)]
        singleton = [(11,2), (3,9), (8,2), (6,1)]

        points_by_color = {
            'bd1038': {
                'xy': horizontal + \
                        vertical + \
                        diagonal_se + \
                        diagonal_ne + \
                        singleton,
            },
            '0896d7': {
                'xy': [
                    # These should not get picked up
                    # even though they run in other directions
                    # to the red lines
                    (2,3), (3,3), (4,3), (5,3),
                    (4,8), (4,9), (4,10),
                    (10,6), (10,7), (10,8),
                ],
            },
        }

        for point in horizontal:
            self.assertEqual(
                'horizontal',
                get_line_direction(point[0], point[1], 'bd1038', points_by_color),
            )

        for point in vertical:
            self.assertEqual(
                'vertical',
                get_line_direction(point[0], point[1], 'bd1038', points_by_color),
            )

        for point in diagonal_se:
            self.assertEqual(
                'diagonal-se',
                get_line_direction(point[0], point[1], 'bd1038', points_by_color),
            )

        for point in diagonal_ne:
            self.assertEqual(
                'diagonal-ne',
                get_line_direction(point[0], point[1], 'bd1038', points_by_color),
            )

        for point in singleton:
            self.assertEqual(
                'singleton',
                get_line_direction(point[0], point[1], 'bd1038', points_by_color),
            )

    def test_get_connected_stations(self):

        """ Confirm that metromap_utils.get_connected_stations
            returns connected stations along a SINGLE direction,
            in the direction where there are the most stations,
            to facilitate drawing connected stations as a capsule or rect

            Eligibility is determined by being rect,rect-round, or circles-thin.

            No eligible adjacent points? singleton
            More than one direction w/ an equal number of points? conflicting
            Interior station that shouldn't be drawn? internal
        """

        stations = [
            # 4 vertical
            {'xy': (1,1), 'style': 'circles-thin', 'expected': (1,4)},
            {'xy': (1,2), 'style': 'rect', 'expected': 'internal'},
            {'xy': (1,3), 'style': 'rect-round', 'expected': 'internal'},
            {'xy': (1,4), 'style': 'rect-round', 'expected': 'internal'},

            # 3 horizontal (including 1,1),
            #   but doesn't know 1,1 is drawn vertically.
            # Might at some point be worth changing this,
            #   but I expect it's a weird corner case,
            #   and it's already added so much complexity
            {'xy': (2,1), 'style': 'rect', 'expected': 'internal'},
            {'xy': (3,1), 'style': 'rect', 'expected': 'internal'},

            # 3 diagonal-se
            {'xy': (3,3), 'style': 'rect', 'expected': (5,5)},
            {'xy': (4,4), 'style': 'rect', 'expected': 'internal'},
            {'xy': (5,5), 'style': 'rect', 'expected': 'internal'},

            # Even though these connect to the other lines,
            #   these styles aren't eligible
            {'xy': (1,5), 'style': 'wmata', 'expected': 'singleton'},
            {'xy': (6,6), 'style': 'circles-lg', 'expected': 'singleton'},

            # 3 Horizontal
            {'xy': (11,1), 'style': 'rect', 'expected': (13,1)},
            {'xy': (12,1), 'style': 'rect', 'expected': 'internal'},
            {'xy': (13,1), 'style': 'rect', 'expected': 'internal'},

            # 1 conflicting, because it could connect in any of: NW, N, NE
            {'xy': (12,2), 'style': 'rect', 'expected': 'conflicting'},
        ]

        for station in stations:
            result = get_connected_stations(station['xy'][0], station['xy'][1], stations)
            if isinstance(result, dict):
                self.assertEqual(result['x1'], station['expected'][0])
                self.assertEqual(result['y1'], station['expected'][1])
            else:
                self.assertEqual(result, station['expected'])
