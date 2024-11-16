import itertools
import json

from django.template import Context, Template

from .validator import VALID_XY, ALLOWED_MAP_SIZES, ALLOWED_ORIENTATIONS

# For use with data version 2
SVG_TEMPLATE = Template('''
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {{ canvas_size|default:80 }} {{ canvas_size|default:80 }}">
{% spaceless %}
{% load metromap_utils %}
{% if stations %}
    <style>text { font: 1px Helvetica; font-weight: 600; white-space: pre; dominant-baseline: central; } line { stroke-width: {{ line_size|default:1 }}; fill: none; stroke-linecap: round; stroke-linejoin: round; }{% for hex, class_name in color_map.items %} .{{ class_name }} { stroke: #{{ hex }} }{% endfor %}</style>
    {% get_station_styles_in_use stations default_station_shape line_size %}
{% else %}
    <style>line { stroke-width: {{ line_size|default:1 }}; fill: none; stroke-linecap: round; stroke-linejoin: round; }{% for hex, class_name in color_map.items %} .{{ class_name }} { stroke: #{{ hex }} }{% endfor %}</style>
{% endif %}
    {% for color, shapes in shapes_by_color.items %}
        {% for line in shapes.lines %}
            <line class="{% map_color color color_map %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}"/>
        {% endfor %}
        {% for point in shapes.points %}
            {% if default_station_shape == 'rect' %}
                <rect x="{{ point.0|add:-0.5 }}" y="{{ point.1|add:-0.5 }}" w="1" h="1" fill="#{{ color }}" />
            {% else %}
                <circle cx="{{ point.0 }}" cy="{{ point.1 }}" r="{{ point.size|default:1 }}" fill="#{{ color }}" />
            {% endif %}
        {% endfor %}
    {% endfor %}
{% endspaceless %}
</svg>
''')

# For use with data_version >= 3
SVG_TEMPLATE_V3 = Template('''
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {{ canvas_size|default:80 }} {{ canvas_size|default:80 }}">
{% spaceless %}
{% load metromap_utils %}
{% if stations %}
    <style>text { font: 1px Helvetica; font-weight: 600; white-space: pre; dominant-baseline: central; } line { stroke-width: {{ line_size|default:1 }}; fill: none; stroke-linecap: round; stroke-linejoin: round; }{% for hex, class_name in color_map.items %} .{{ class_name }} { stroke: #{{ hex }} }{% endfor %} {% get_line_width_styles_for_svg_style shapes_by_color %}</style>
    {% get_station_styles_in_use stations default_station_shape line_size %}
{% else %}
    <style>line { stroke-width: {{ line_size|default:1 }}; fill: none; stroke-linecap: round; stroke-linejoin: round; }{% for hex, class_name in color_map.items %} .{{ class_name }} { stroke: #{{ hex }} }{% endfor %} {% get_line_width_styles_for_svg_style shapes_by_color %}</style>
{% endif %}
{% if shapes_by_color|has_line_style:"color_outline" %}
    <filter id="fco" filterUnits="userSpaceOnUse">
        <feBlend in="SourceGraphic" in2="SourceGraphic" mode="screen"/>
    </filter>
{% endif %}
    {% for color, line_width_style in shapes_by_color.items %}
        {% for width_style, shapes in line_width_style.items %}
            {% for line in shapes.lines %}
                {% if 'hollow' in width_style or 'color_outline' in width_style %}
                    <mask id="k{{ forloop.parentloop.parentloop.counter }}-{{ forloop.parentloop.counter }}-{{ forloop.counter }}" maskUnits="userSpaceOnUse">
                        <line class="{% get_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" stroke="#fff"/>
                        <line class="{% get_masked_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" stroke="#000"/>
                    </mask>
                    {% if 'color_outline' in width_style %}
                        <line class="{% map_color color color_map %} {% get_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" filter="url(#fco)"/>
                    {% endif %}
                    <line class="{% map_color color color_map %} {% get_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" mask="url(#k{{ forloop.parentloop.parentloop.counter }}-{{ forloop.parentloop.counter }}-{{ forloop.counter }})"/>
                {% elif 'stripes' in width_style %}
                    <mask id="k{{ forloop.parentloop.parentloop.counter }}-{{ forloop.parentloop.counter }}-{{ forloop.counter }}" maskUnits="userSpaceOnUse">
                        <line class="{% get_line_class_from_width_style width_style line_size True %} {% if 'wide_stripes' in width_style %}sl-sq{% else %}sl-b{% endif %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" stroke="#fff"/>
                        <line class="{% get_masked_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" stroke="#000"/>
                    </mask>
                    <line class="{% map_color color color_map %} {% get_line_class_from_width_style width_style line_size True %} {% if 'wide_stripes' in width_style %}sl-sq{% else %}sl-b{% endif %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}" mask="url(#k{{ forloop.parentloop.parentloop.counter }}-{{ forloop.parentloop.counter }}-{{ forloop.counter }})"/>
                    <line class="{% map_color color color_map %} {% get_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}"/>
                {% else %}
                    <line class="{% map_color color color_map %} {% get_line_class_from_width_style width_style line_size %}" x1="{{ line.0 }}" y1="{{ line.1 }}" x2="{{ line.2 }}" y2="{{ line.3 }}"/>
                {% endif %}
            {% endfor %}
            {% for point in shapes.points %}
                {% if default_station_shape == 'rect' %}
                    <rect x="{{ point.0|add:-0.5 }}" y="{{ point.1|add:-0.5 }}" w="1" h="1" fill="#{{ color }}" />
                {% else %}
                    <circle cx="{{ point.0 }}" cy="{{ point.1 }}" r="{{ point.size|default:1 }}" fill="#{{ color }}" />
                {% endif %}
            {% endfor %}
        {% endfor %}
    {% endfor %}
{% endspaceless %}
</svg>
''')

STATIONS_SVG_TEMPLATE = Template('''
{% spaceless %}
{% load metromap_utils %}
{% for station in stations %}
    {% station_marker station default_station_shape line_size points_by_color stations data_version %}
    {% station_text station %}
{% endfor %}
{% endspaceless %}
</svg>
''')

# Largest square worth checking with find_squares()
LARGEST_SQUARE = 6
USE_SQUARES_THRESHOLD = 1000 # If there are this many points in a single color, use squares even if the line width is thin

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

    if not isinstance(mapdata, dict):
        mapdata = json.loads(mapdata)

    color_map = {}
    points_by_color = {}
    stations = []
    highest_seen = 0
    map_size = 80
    allowed_sizes = {
        'classic': {
            # Order matters
            1: reversed(ALLOWED_MAP_SIZES),
            2: reversed(ALLOWED_MAP_SIZES),
            3: reversed(ALLOWED_MAP_SIZES),
        }
    }
    allowed_sizes = allowed_sizes[map_type][data_version]

    linewidthstyles_by_xy = {}

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
                        'xy': (int(x), int(y)),
                        'color': line_color,
                    }
                    try:
                        station_data['orientation'] = int(station.get('orientation', ALLOWED_ORIENTATIONS[0]))
                    except Exception:
                        station_data['orientation'] = ALLOWED_ORIENTATIONS[0]
                    if station.get('transfer'):
                        station_data['transfer'] = 1
                    style = station.get('style')
                    if style:
                        station_data['style'] = style
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

    elif map_type == 'classic' and data_version == 2:
        # The point here is to convert from the data format optimized for JS
        #   to the format best for SVG
        colors_by_xy = {}

        default_station_shape = mapdata['global'].get('style', {}).get('mapStationStyle', 'wmata')

        for line_color in mapdata['points_by_color']:
            for x in mapdata['points_by_color'][line_color]['xys']:
                for y in mapdata['points_by_color'][line_color]['xys'][x]:
                    x = str(x)
                    y = str(y)
                    if x not in VALID_XY or y not in VALID_XY:
                        continue

                    if mapdata['points_by_color'][line_color]['xys'][x][y] != 1:
                        continue

                    if line_color not in points_by_color:
                        points_by_color[line_color] = {
                            'xy': set(),
                        }

                    colors_by_xy[f'{x},{y}'] = line_color

                    x = int(x)
                    y = int(y)

                    if x > highest_seen:
                        highest_seen = x
                    if y > highest_seen:
                        highest_seen = y

                    points_by_color[line_color]['xy'].add((x, y))

    elif map_type == 'classic' and data_version == 3:
        colors_by_xy = {}

        default_station_shape = mapdata['global'].get('style', {}).get('mapStationStyle', 'wmata')

        for line_color in mapdata['points_by_color']:
            for width_style in mapdata['points_by_color'][line_color]:
                for x in mapdata['points_by_color'][line_color][width_style]:
                    for y in mapdata['points_by_color'][line_color][width_style][x]:
                        x = str(x)
                        y = str(y)
                        if x not in VALID_XY or y not in VALID_XY:
                            continue

                        if mapdata['points_by_color'][line_color][width_style][x][y] != 1:
                            continue

                        if line_color not in points_by_color:
                            points_by_color[line_color] = {
                                width_style: set(),
                            }
                        elif width_style not in points_by_color[line_color]:
                            points_by_color[line_color][width_style] = set()

                        colors_by_xy[f'{x},{y}'] = line_color
                        linewidthstyles_by_xy[f'{x},{y}'] = width_style

                        x = int(x)
                        y = int(y)

                        if x > highest_seen:
                            highest_seen = x
                        if y > highest_seen:
                            highest_seen = y

                        points_by_color[line_color][width_style].add((x, y))

    if map_type == 'classic' and data_version >= 2:

        default_line_width = mapdata['global'].get('style', {}).get('mapLineWidth', 1)
        default_line_style = mapdata['global'].get('style', {}).get('mapLineStyle', 'solid')
        default_line_width_style = f'{default_line_width}-{default_line_style}'

        for x in mapdata['stations']:
            for y in mapdata['stations'][x]:
                if x not in VALID_XY or y not in VALID_XY:
                    continue

                station = mapdata['stations'][x][y]
                station_data = {
                    'name': station.get('name', ''),
                    'orientation': station.get('orientation', 0),
                    'xy': (int(x), int(y)),
                    'color': colors_by_xy[f'{x},{y}'],
                    'line_width_style': linewidthstyles_by_xy.get(f'{x},{y}', default_line_width_style)
                }
                if station.get('transfer'):
                    station_data['transfer'] = 1
                station_data['style'] = station.get('style', default_station_shape)
                stations.append(station_data)


    for size in allowed_sizes:
        if highest_seen < size:
            map_size = size

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
            a vertically-adjacent point
            a horizontally-adjacent point
            a diagonally-adjcaent point

        This wouldn't be efficient if all_points
            was ALL possible points (but it isn't),
            and would be more direct to generate
            the nearest 8 neighboring points
            and check whether pt is in that,
            but that doesn't account for whether those points
            are actually in this color.
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

def get_svg_from_shapes_by_color(shapes_by_color, map_size, line_size, default_station_shape, points_by_color, stations=False, data_version=3):

    """ Finally, let's draw SVG from the sorted shapes by color.

        Note: points_by_color shouldn't be used directly to draw, but it's necessary
            to check line direction and station adjacency for diagonal rectangle stations
            and connecting stations

        Although stations are drawn separately,
            the SVG's style will want to know whether they're present,
            so don't delete stations from the context or the argument
    """

    context = {
        'shapes_by_color': shapes_by_color,
        'points_by_color': points_by_color,
        'canvas_size': map_size,
        'stations': stations or [],
        'line_size': line_size,
        'default_station_shape': default_station_shape,
        'color_map': {color: f'c{index}' for index, color in enumerate(points_by_color.keys())},
    }

    if data_version >= 3:
        return SVG_TEMPLATE_V3.render(Context(context))
    else:
        return SVG_TEMPLATE.render(Context(context))

def add_stations_to_svg(thumbnail_svg, line_size, default_station_shape, points_by_color, stations, data_version):

    """ This allows me to avoid generating the map SVG twice
        (once for thumbnails, once for stations)

        In theory, why have an SVG thumbnail at all?
        In practice, the byte size difference is meaningful for load times,
        especially when deciding whether to display a lower-quality PNG,
        and when displaying a lot of thumbnails on a screen.
    """

    context = {
        'line_size': line_size,
        'default_station_shape': default_station_shape,
        'points_by_color': points_by_color,
        'stations': stations,
        "data_version": data_version,
    }

    return thumbnail_svg.replace('</svg>', STATIONS_SVG_TEMPLATE.render(Context(context)))

def find_squares(points_this_color, width=5, already_found=None):

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

    if not already_found:
        already_found = []

    ptc_x = points_this_color['x']
    for pt in already_found:
        if pt[0] in ptc_x:
            ptc_x.remove(pt[0])
    counts_x = {x: ptc_x.count(x) for x in set(ptc_x)}
    counts_x = {x: count for x, count in counts_x.items() if count >= width}

    # Trivially, there aren't enough points to form a square of this size
    if not counts_x:
        return [], []

    # Repeat for y
    ptc_y = points_this_color['y']
    for pt in already_found:
        if pt[1] in ptc_y:
            ptc_y.remove(pt[1])
    counts_y = {y: ptc_y.count(y) for y in set(ptc_y)}
    counts_y = {y: count for y, count in counts_y.items() if count >= width}

    if not counts_y:
        return [], []

    # Excluding trivials was the easy part.
    ptc_xy = points_this_color['xy']
    potentials = sorted([
        xy for xy in ptc_xy
        if xy[0] in counts_x and xy[1] in counts_y and xy not in already_found
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

def find_lines(points_this_color):

    """ Better drawing algorithm,
            returning a small number of lines,
            and still has fidelity with classic omnidirectional style
    """

    directions = 'E S NE SE' # Don't need to draw N, W, NW, SW
    skip_points = {d: set() for d in directions.split()}

    lines = set()
    singletons = set()
    not_singletons = set()

    for direction in directions.split():
        for point in sorted(points_this_color):
            x, y = point

            if point in skip_points[direction]:
                continue
            endpoint = find_endpoint_of_line(x, y, points_this_color, direction)
            if endpoint:
                lines.add((x, y, endpoint['x1'], endpoint['y1']))
                not_singletons.add((x,y))
                not_singletons.add((endpoint['x1'], endpoint['y1']))
                for pt in endpoint['between']:
                    not_singletons.add(pt)
                    skip_points[direction].add(pt)
            elif point in not_singletons:
                # This might not make a line in this direction,
                #   but it does connect to a line in SOME direction,
                #   so it's not a singleton
                pass
            else:
                singletons.add(point)

    # Some of the points that we thought were singletons at the time might not be,
    #   if we haven't processed those points yet
    return lines, (singletons - not_singletons)

def find_endpoint_of_line(x, y, points, direction):

    """ Given x, y, and a set of coordinate pairs (points),
        find the endpoint of the line originating at (x, y)
        for a given direction
    """

    between = [(x, y)]

    # 'E S NE SE SW' # Don't need to draw N, W, NW
    directions = {
        'E': {'dx': 1, 'dy': 0},
        'S': {'dx': 0, 'dy': 1},
        'NE': {'dx': 1, 'dy': -1},
        'SE': {'dx': 1, 'dy': 1},
        'SW': {'dx': -1, 'dy': 1},
    }

    dx = directions[direction]['dx']
    dy = directions[direction]['dy']

    (x1, y1) = (x + dx, y + dy)

    if (x1, y1) not in points:
        return

    while (x1, y1) in points:
        between.append((x1, y1))
        (x1, y1) = (x1 + dx, y1 + dy)

    return {
        # "between" is maybe a misnomer;
        #   it's the points we don't have to check in this direction,
        #   which includes the starting and ending points
        'between': between,
        'x1': between[-1][0],
        'y1': between[-1][1],
    }

def flatten_nested(l):

    """ Flattens a nested list (by one level)
    """

    return list(itertools.chain.from_iterable(l))
