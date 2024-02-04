import itertools
import json

from django.template import Context, Template
from PIL import Image, ImageDraw

from .validator import VALID_XY

SVG_TEMPLATE = Template('''
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {{ canvas_size|default:80 }} {{ canvas_size|default:80 }}">
{#{% spaceless %}#} {# DEBUG #}
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
        {% for square in shapes.square_interior_points %}
            <rect x="{{ square.0.0|add:-0.5 }}" y="{{ square.0.1|add:0.5 }}" width="{{ square|length|square_root|add:2 }}" height="{{ square|length|square_root|add:2 }}" fill="#{{ color }}" />
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
{#{% endspaceless %}#}
</svg>
''')

# Largest square worth checking with find_squares()
LARGEST_SQUARE = 6

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
                        'x': [],
                        'y': [],
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

                points_by_color[line_color]['x'].append(x)
                points_by_color[line_color]['y'].append(y)
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
        'S': (x, y + 1),
        'N': (x, y - 1),
        'E': (x + 1, y),
        'W': (x - 1, y),
        'SE': (x + 1, y + 1),
        'NE': (x + 1, y - 1),
        'SW': (x - 1, y + 1),
        'NW': (x - 1, y - 1),
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
        points_to_check = sorted(points_by_color[color]['xy'])

        shapes_by_color[color] = {
            'lines': [],
            'points': [],
            'all_lines': [], # NOT IN USE, YET -- TODO
            'square_interior_points': [],
        }

        pbc = {k: list(v) for k, v in points_by_color[color].items()}
        for sq_size in range(LARGEST_SQUARE, 2, -1):
            exterior, interior = find_squares(pbc, sq_size)
            if exterior and interior:
                for outline in exterior:
                    shapes_by_color[color]['lines'].append(outline)
                    shapes_by_color[color]['all_lines'].append(outline)

                for square in interior:
                    shapes_by_color[color]['square_interior_points'].append(sorted(square))

                for pt in itertools.chain(*interior):

                    points_to_check.remove(pt)
                    pbc['xy'].remove(pt)
                    pbc['x'].remove(pt[0])
                    pbc['y'].remove(pt[1])

                for pt in itertools.chain(*exterior):
                    points_to_check.remove(pt)
                    pbc['xy'].remove(pt)
                    pbc['x'].remove(pt[0])
                    pbc['y'].remove(pt[1])

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

                lines.append(current_line)
                shapes_by_color[color]['lines'].extend(lines)
                shapes_by_color[color]['all_lines'].extend(lines)

    # If one line overlaps with another,
    #   add those points
    # TODO: Note: this isn't perfect, and misses when one line's start
    #   intersects with another line's middle (see PyKsuUAq, 6VZ7tG6S)
    # 40,24 shouldnt appear 6x at the end but does thx to this
    for color in shapes_by_color:
        line_endings = []

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

    # Reduce straight lines at the end so we don't impede other connections
    for color in shapes_by_color:
        for index, line in enumerate(shapes_by_color[color]['lines']):
            shapes_by_color[color]['lines'][index] = reduce_straight_line(line)

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
        canvas_size = 1920
        line_size = line_size * 8
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

        if stations:
            for station in stations:
                x, y = station['xy']
                x = int(x)
                y = int(y)
                circle = [(x - 0.5) * line_size, (y - 0.5) * line_size]
                circle.extend([
                    (x + 0.5) * line_size,
                    (y + 0.5) * line_size,
                ])
                if station['transfer']:
                    # TODO" this doesnt show up
                    # draw.ellipse(circle, fill='#000', width=1.2 * line_size)
                    # draw.ellipse(circle, fill='#fff', width=.9 * line_size)
                    draw.ellipse(circle, fill='#fff', outline='#000', width=round(line_size / 2.5))
                # This has a few problems --- the circle is off-center
                # and the black circle outline isn't bold enough
                # Also, width cant be a float
                # draw.ellipse(circle, fill='#000', width=.6 * line_size)
                draw.ellipse(circle, fill='#fff', outline='#000', width=round(line_size / 5))
                # draw.arc(circle, start=0, end=360, fill='#000', width=round(1.2 * line_size))

                # draw.arc(circle, start=0, end=360, fill=)

                # ImageDraw.arc(xy, start, end, fill=None, width=0)[source]
                # ctx.arc(x * gridPixelMultiplier, y * gridPixelMultiplier, gridPixelMultiplier * .6, 0, Math.PI * 2, true);

                # TODO: Station text
                # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.ImageDraw.text

                """
                {% if station.transfer %}
                    <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r="1.2" fill="#000" />
                    <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r=".9" fill="#fff" />
                {% endif %}
                <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r=".6" fill="#000" />
                <circle cx="{{ station.xy.0 }}" cy="{{ station.xy.1 }}" r=".3" fill="#fff" />
                {% station_text station %}
                """

        img.save(filename, 'PNG')

def find_squares(points_this_color, width=5):

    """ Must be called before get_connected_points, because this is meant to
        prevent recursion depth problems on maps with a lot of "terrain"

        Returns two lists:
            a list of the outlining points of each square
            a list of the interior points of each square

        Can call mulitple times to get ever-smaller (n-2) squares, for example:
            width=5 gets a 5x5 square with a 3x3 interior
            width=4 gets a 4x4 square with a 2x2 interior
            width=3 gets a 3x3 square with a 1x1 interior
    """

    ptc_x = points_this_color['x']
    counts_x = {x: ptc_x.count(x) for x in set(ptc_x)}
    counts_x = {x: count for x, count in counts_x.items() if count >= width}

    # Trivially, there aren't enough points to form a square of this size
    if not counts_x:
        return [], []

    # Repeat for y
    ptc_y = points_this_color['y']
    counts_y = {y: ptc_y.count(y) for y in set(ptc_y)}
    counts_y = {y: count for y, count in counts_y.items() if count >= width}

    if not counts_y:
        return [], []

    # Excluding trivials was the easy part.
    ptc_xy = points_this_color['xy']
    potentials = sorted([
        xy for xy in ptc_xy
        if xy[0] in counts_x and xy[1] in counts_y
    ])

    # Last trivial check
    if len(potentials) < width * width:
        return [], []

    squares_ext = []
    squares_int = []

    while potentials:
        xy = potentials[0]

        needed_for_square_exterior = []
        needed_for_square_interior = []
        for x in range(width):
            for y in range(width):
                if x in (0, width - 1) or y in (0, width - 1):
                    needed_for_square_exterior.append((xy[0] + x, xy[1] + y))
                else:
                    needed_for_square_interior.append((xy[0] + x, xy[1] + y))

        exterior = all([pt in potentials for pt in needed_for_square_exterior])
        interior = all([pt in potentials for pt in needed_for_square_interior])

        if exterior and interior:
            squares_ext.append(needed_for_square_exterior)
            squares_int.append(needed_for_square_interior)
            for pt in needed_for_square_exterior:
                potentials.remove(pt)
            for pt in needed_for_square_interior:
                potentials.remove(pt)
        else:
            potentials.remove(xy)

    return squares_ext, squares_int


