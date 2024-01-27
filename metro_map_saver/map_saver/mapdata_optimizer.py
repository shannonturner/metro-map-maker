import json

from django.template import Context, Template

from .validator import VALID_XY

# TODO: Shouldn't always be 240/240, but instead should flex based on proper size
SVG_TEMPLATE = Template('''
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {{ canvas_size|default:80 }} {{ canvas_size|default:80 }}">
{% spaceless %}
    {% for color, shapes in shapes_by_color.items %}
        {% for line in shapes.lines %}
            <polyline points="{% for coords in line %}{{ coords.0 }},{{ coords.1 }} {% endfor %}" stroke="#{{ color }}" stroke-width="{{ line_size|default:1 }}" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        {% endfor %}
        {% for point in shapes.points %}
            <circle cx="{{ point.0 }}" cy="{{ point.1 }}" r="{{ point.size|default:1 }}" fill="#{{ color }}" />
        {% endfor %}
    {% endfor %}
{% endspaceless %}
</svg>
''') # TODO: Add Stations!

def sort_points_by_color(mapdata, map_type='classic', data_version=1):

    """ Given a JSON of mapdata,
            return a JSON of points by color
            in the format:
                {
                    1: {
                        x: [...], # x coordinates for color 1 only
                        y: [...], # y coordinates for color 1 only
                        xy: [...], # x,y pairs 
                    }
                }
    """

    mapdata = json.loads(mapdata)

    color_map = {}
    points_by_color = {}
    highest_seen = 0
    map_size = 80
    allowed_sizes = {
        'classic': {
            1: [80, 120, 160, 200, 240],
        }
    }
    allowed_sizes = allowed_sizes[map_type][data_version]

    if map_type == 'classic' and data_version == 1:
        # Ex: [0][1]['line']: 'bd1038'
        for x in sorted(mapdata):
            if x not in VALID_XY:
                continue
            for y in sorted(mapdata[x]):
                if y not in VALID_XY:
                    continue

                line_color = mapdata[str(x)][y].get('line')
                if not line_color:
                    continue

                if line_color not in points_by_color:
                    points_by_color[line_color] = {
                        # 'x': [],
                        # 'y': [],
                        'xy': [],
                    }

                # Add the points
                x = int(x)
                y = int(y)

                if x > highest_seen:
                    highest_seen = x
                if y > highest_seen:
                    highest_seen = y

                # TODO: Consider: Might be interesting optimization I can do with X alone or Y alone,
                #   worth holding this idea for later
                # points_by_color[line_color]['x'].append(x)
                # points_by_color[line_color]['y'].append(y)
                points_by_color[line_color]['xy'].append((x, y))

        for size in allowed_sizes:
            if highest_seen < size:
                map_size = size
    elif map_type == 'classic' and data_version == 2:
        raise NotImplementedError('TODO')

    return points_by_color, map_size

def get_connected_points(x, y, points, connected=None, checked=None, check_next=None):

    """ Recursively find all connected points for x, y.

        This is useful if points is a list of 2-tuple (x, y) coordinate pairs
            pre-sorted by a single color.

        May hit recursion depth if more than 1k points are connected,
            in which case some pre-optimizations should be done.
    """

    if not connected:
        connected = [(x, y)]

    if not checked:
        checked = []

    if not check_next:
        check_next = []

    to_check = {
        'SE': (x + 1, y + 1),
        'NE': (x + 1, y - 1),
        'SW': (x - 1, y + 1),
        'NW': (x - 1, y - 1),
        'E': (x + 1, y),
        'W': (x - 1, y),
        'N': (x, y - 1),
        'S': (x, y + 1),
    }

    for direction, coords in to_check.items():

        if coords[0] < 0 or coords[1] < 0:
            continue

        if coords in checked:
            continue

        if coords not in points:
            checked.append(coords)
            continue

        if coords in points and coords not in connected:
            connected.append(coords)
            checked.append(coords)
            check_next.append(coords)
    
    while check_next:
        coords = check_next.pop(0)
        return get_connected_points(
            coords[0],
            coords[1],
            points,
            connected,
            checked,
            check_next,
        )

    return connected

def get_shapes_from_points(points_by_color):

    """ One we have points sorted by color,
            we need to sort them into shapes
            based on whether they're adjacent.

        Currently sorts into nested lists of lines (made of points)
            and singleton points; though could make this smarter
            by identifying other types of shapes,
            especially squares and similar.
    """

    shapes_by_color = {}

    for color in points_by_color:
        points_to_check = points_by_color[color]['xy']
        shapes_by_color[color] = {'lines': [], 'points': []}
        while points_to_check:
            point = points_to_check.pop(0)
            shape = get_connected_points(*point, points_to_check)
            if len(shape) == 1:
                shapes_by_color[color]['points'].append(shape[0])
            else:
                # Ensure that all points in this shape are actually adjacent.
                # We already know they're connected.
                lines = []
                current_line = []
                while shape:
                    if not current_line:
                        pt = shape.pop(0)
                    else:
                        # We need to continue looking for adjacent points
                        #   from the most recently-added point
                        pt = current_line[-1]

                    if pt != point and pt in points_to_check:
                        points_to_check.remove(pt)

                    if pt not in current_line:
                        current_line.append(pt)

                    if not shape:
                        # We just consumed the last point
                        pass
                    elif shape:
                        # Try to get a horizontally, vertically,
                        #   or diagonally adjacent line
                        adjacent = get_adjacent_point(pt, shape)

                        # LEAVING OFF, J25 8AM:
                        # "1,61 2,60 1,62 1,63 3,60
                        # NOTE THAT THESE POINTS ARE NOT ACTUALLY ADJACENT -- 2, 60 IS NOT ADJACENT TO 1, 62.
                        # WHAT GIVES?

                        if adjacent:
                            shape.remove(adjacent)
                            points_to_check.remove(adjacent)
                            current_line.append(adjacent)
                        else:
                            lines.append(current_line)
                            current_line = []

                lines.append(current_line)
                shapes_by_color[color]['lines'].extend(lines)

    return shapes_by_color

def get_adjacent_point(pt, all_points):

    """ Attempts to find:
            a horizontally-adjacent point
            a vertically-adjacent point
            a diagonally-adjcaent point
    """

    for point in all_points:
        dx = abs(pt[0] - point[0])
        dy = abs(pt[1] - point[1])

        if dx == 0 and dy == 1:
            # If the x-coordinate hasn't changed,
            #   but the y-coordinate is off by 1,
            #   this is a vertical line
            return point

        if dx == 1 and dy == 0:
            # If the x-coordinate is off by 1,
            #   but the y-coordinate hasn't changed,
            #   this is a horizontal line
            return point

        if dx == 1 and dy == 1:
            # If both x and y are off by 1,
            #   this is a diagonal line 
            return point

def get_svg_from_shapes_by_color(shapes_by_color, map_size, stations=False):

    """ Finally, let's draw SVG from the sorted shapes by color.

        If stations=True, draw stations;
            otherwise omit them (nicer for thumbnails)
    """

    # TODO: Stations
    # TODO: Sizing and other 

    context = {
        'shapes_by_color': shapes_by_color,
    }

    return SVG_TEMPLATE.render(Context(context))

def test_make_svg():
    from map_saver.models import SavedMap
    m = SavedMap.objects.get(urlhash='QMEGk9gq')
    from map_saver.mapdata_optimizer import (
        sort_points_by_color,
        get_shapes_from_points,
        get_svg_from_shapes_by_color,
    )
    points_by_color = sort_points_by_color(m.mapdata)
    shapes_by_color = get_shapes_from_points(points_by_color)
    svg = get_svg_from_shapes_by_color(shapes_by_color)
    print(svg)
    with open('/Users/shannon/Downloads/mmm-test-t-a1.svg', 'w') as svgfile:
        svgfile.write(svg)
    return 'yay'

""" J24, GETTING VERY CLOSE!
from map_saver.models import SavedMap
m = SavedMap.objects.get(urlhash='QMEGk9gq')
from map_saver.mapdata_optimizer import (
    sort_points_by_color,
    get_shapes_from_points,
    get_svg_from_shapes_by_color,
)
points_by_color = sort_points_by_color(m.mapdata)
shapes_by_color = get_shapes_from_points(points_by_color)
svg = get_svg_from_shapes_by_color(shapes_by_color)
print(svg)
with open('/Users/shannon/Downloads/mmm-test-t-a1.svg', 'w') as svgfile:
    svgfile.write(svg)

from map_saver.mapdata_optimizer import test_make_svg; test_make_svg()

from map_saver.mapdata_optimizer import SVG_TEMPLATE, Context
"""

# def annotate_counts(lst):

#     """ Given a list, return a dict of coords by counts.

#         This can be useful because 
#     """

# if line_color in color_map.values():
#     # Allow bidirectional lookup
#     color_key = color_map[line_color]
# else:
#     color_key = (len(color_map) / 2) + 1
#     color_map[color_key] = line_color
#     color_map[line_color] = color_key