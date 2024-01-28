import json

from django.template import Context, Template
from PIL import Image, ImageDraw

from .validator import VALID_XY

SVG_TEMPLATE = Template('''
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {{ canvas_size|default:80 }} {{ canvas_size|default:80 }}">
{% spaceless %}
{% load metromap_utils %}
{% if stations %}
    <style>text { font: 1px Helvetica; font-weight: 600; white-space: pre; }</style>
{% endif %}
    {% for color, shapes in shapes_by_color.items %}
        {% for line in shapes.lines %}
            <polyline points="{% for coords in line %}{{ coords.0 }},{{ coords.1 }} {% endfor %}" stroke="#{{ color }}" stroke-width="{{ line_size|default:1 }}" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        {% endfor %}
        {% for point in shapes.points %}
            <circle cx="{{ point.0 }}" cy="{{ point.1 }}" r="{{ point.size|default:1 }}" fill="#{{ color }}" />
        {% endfor %}
    {% endfor %}
    {% for station in stations %}
        {% if station.transfer %}
            <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r="1.2" fill="#000" />
            <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r=".9" fill="#fff" />
        {% endif %}
        <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r=".6" fill="#000" />
        <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r=".3" fill="#fff" />
        {% station_text station %}
    {% endfor %}
{% endspaceless %}
</svg>
''')

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
    stations = []
    highest_seen = 0
    map_size = 80
    allowed_sizes = {
        'classic': {
            # Order matters
            1: [240, 200, 160, 120, 80],
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

                station = mapdata[str(x)][y].get('station')
                if station:
                    station_data = {
                        'name': station.get('name', ''),
                        'lines': station.get('lines', []),
                        'transfer': station.get('transfer', 0),
                        'orientation': station.get('orientation', 0),
                        'xy': (int(x), y),
                    }
                    stations.append(station_data)

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

    return points_by_color, stations, map_size

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

                        if adjacent:
                            shape.remove(adjacent)
                            points_to_check.remove(adjacent)
                            current_line.append(adjacent)
                        else:
                            lines.append(current_line)
                            current_line = []

                lines.append(reduce_straight_line(current_line))
                shapes_by_color[color]['lines'].extend(lines)

    # If the start/end of one line overlaps with another,
    #   add those points
    line_endings = []
    for color in shapes_by_color:
        for line in shapes_by_color[color]['lines']:
            line_endings.append(line[0])
            line_endings.append(line[-1])

        for index, line in enumerate(shapes_by_color[color]['lines']):
            line_start = line[0]
            line_end = line[-1]

            for connect_to in line_endings:
                if line_start == connect_to:
                    continue
                elif line_end == connect_to:
                    continue

                if is_adjacent(line_start, connect_to):
                    shapes_by_color[color]['lines'][index].insert(0, connect_to)

                if is_adjacent(line_end, connect_to):
                    shapes_by_color[color]['lines'][index].append(connect_to)

                # It's adjacent with itself, like a diamond
                if is_adjacent(line_start, line_end):
                    shapes_by_color[color]['lines'][index].append(line_start)

    return shapes_by_color

def is_adjacent(point1, point2):

    """ Helper function to check whether
            point1 is adjcaent to point2
    """

    dx = abs(point1[0] - point2[0])
    dy = abs(point1[1] - point2[1])

    if dx == 0 and dy == 1:
        # If the x-coordinate hasn't changed,
        #   but the y-coordinate is off by 1,
        #   this is a vertical line
        return point2

    if dx == 1 and dy == 0:
        # If the x-coordinate is off by 1,
        #   but the y-coordinate hasn't changed,
        #   this is a horizontal line
        return point2

    if dx == 1 and dy == 1:
        # If both x and y are off by 1,
        #   this is a diagonal line
        return point2

def get_adjacent_point(pt, all_points):

    """ Attempts to find:
            a horizontally-adjacent point
            a vertically-adjacent point
            a diagonally-adjcaent point
    """

    for point in all_points:
        if is_adjacent(pt, point):
            return point

def reduce_straight_line(line):

    """ Reduce a straight line's xy coordinate pairs
        to the smallest-possible representation.

        For example: 1,1 1,2 1,3 1,4 1,5 could be written as 1,1 1,5
    """

    start = line[0]
    end = line[-1]

    all_x = [x for (x, y) in line]
    all_y = [y for (x, y) in line]

    if all_x.count(start[0]) == len(line):
        # x value remains the same for the whole line (vertical)
        return [start, end]
    elif all_y.count(start[1]) == len(line):
        # y value remains the same for the whole line (horizontal)
        return [start, end]

    consecutive = {
        'SE': 1,
        'NE': 1,
        'NW': 1,
        'SW': 1,
    }
    for index, xy in enumerate(line):
        x, y = xy
        if index == len(line) - 1:
            continue
        if x == (line[index + 1][0] + 1) and y == (line[index + 1][1] + 1):
            consecutive['SE'] += 1
        if x == (line[index + 1][0] + 1) and y == (line[index + 1][1] - 1):
            consecutive['NE'] += 1
        if x == (line[index + 1][0] - 1) and y == (line[index + 1][1] - 1):
            consecutive['NW'] += 1
        if x == (line[index + 1][0] - 1) and y == (line[index + 1][1] + 1):
            consecutive['SW'] += 1

    for direction in consecutive:
        if consecutive[direction] == len(line):
            return [start, end]

    # TODO: More complex line shapes with partial horizontal/vertical/diagonals

    # Can't be reduced further
    return line

def get_svg_from_shapes_by_color(shapes_by_color, map_size, stations=False):

    """ Finally, let's draw SVG from the sorted shapes by color.

        If stations=True, draw stations;
            otherwise omit them (nicer for thumbnails)
    """

    context = {
        'shapes_by_color': shapes_by_color,
        'canvas_size': map_size,
        'stations': stations or [],
    }

    return SVG_TEMPLATE.render(Context(context))

def draw_png_from_shapes_by_color(shapes_by_color, urlhash, map_size, filename, stations=False):

    """ For some maps, the PNG may be a smaller filesize.

        TODO: Add support for social sharing image generation since Opengraph doesn't
            support SVG
            ^ this really means TODO: Add stations & text
    """

    line_size = 240 // map_size

    if stations:
        canvas_size = 1200
    else:
        # Thumbnail
        canvas_size = 240

    with Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0)) as img:

        draw = ImageDraw.Draw(img)

        for color in shapes_by_color:
            for line in shapes_by_color[color]['lines']:
                line = [(x * line_size, y * line_size) for x, y in line]
                draw.line(line, fill='#' + color, width=line_size, joint='curve')
            for point in shapes_by_color[color]['points']:
                circle = [point[0] * line_size, point[1] * line_size]
                circle.extend([
                    (point[0] + 1) * line_size, # x1
                    (point[1] + 1) * line_size, # y1
                ])
                draw.ellipse(circle, fill='#' + color, width=1)

        img.save(filename, 'PNG')
