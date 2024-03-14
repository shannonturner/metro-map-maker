from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from map_saver.validator import (
    ALLOWED_ORIENTATIONS,
    ALLOWED_STATION_STYLES,
    ALLOWED_CONNECTING_STATIONS,
    is_hex,
)

import logging
from math import sqrt
from os.path import getmtime

register = template.Library()

logger = logging.getLogger(__name__)

@register.simple_tag
def station_marker(station, default_shape, line_size, points_by_color, stations):

    """ Generate the SVG shape for a station based on
            whether it's a transfer station and what its shape is.

        Consider: some stations could probably be optimized into a single SVG, or at least fewer.

            For example, a WMATA transfer station is currently 4 circles, but could be 2 circles with strokes.

            Only worth doing if it would be a real byte savings and not a loss of image quality / fidelity to the canvas-rendered version.
    """

    assert isinstance(station['xy'][0], int)
    assert isinstance(station['xy'][1], int)

    x = station['xy'][0]
    y = station['xy'][1]

    transfer = station.get('transfer') == 1
    shape = station.get('style', default_shape)
    color = f"#{station['color']}"

    if shape not in ALLOWED_STATION_STYLES:
        logger.error(f"Can't generate SVG for shape: {shape}")
        raise NotImplementedError(f"Can't generate SVG for shape: {shape}")

    svg = []

    # Using a dict for the handling here would be less workable/maintainable,
    #   because of the different handling for transfer stations
    #   and conditional stroke/fills based on line size
    if shape == 'wmata':
        if transfer:
            svg.append(svg_circle(x, y, 1.2, '#000'))
            svg.append(svg_circle(x, y, .9, '#fff'))
        svg.append(svg_circle(x, y, .6, '#000'))
        svg.append(svg_circle(x, y, .3, '#fff'))
    elif shape in ALLOWED_CONNECTING_STATIONS:
        # Set generics, and change as needed
        width = 0.5
        height = 0.5
        x_offset = -0.5
        y_offset = -0.5

        if shape in ('rect-round', 'circles-thin'):
            radius = 0.5 # SVG equivalent for the pill shape
        else:
            radius = False

        line_direction = get_line_direction(x, y, color, points_by_color)
        station_direction = get_connected_stations(x, y, stations)
        draw_as_connected = False

        if station_direction == 'internal':
            return '' # Don't draw this point

        if station.get('transfer'):
            width = 1
            height = 1
            stroke_width = 0.2
        else:
            stroke_width = 0.1

        if line_size >= 0.5 and line_direction != 'singleton':
            stroke = '#000'
            fill = '#fff'
        elif line_direction == 'singleton' and shape == 'rect-round':
            stroke = '#000'
            fill = '#fff'
        elif line_direction == 'singleton' and station_direction == 'singleton' and shape in ('rect', 'rect-round'):
            stroke = '#000'
            fill = color
        else:
            stroke = fill = color

        if station_direction == 'conflicting':
            width = height = 1
        elif isinstance(station_direction, dict):
            # Connect these stations
            draw_as_connected = True
            stroke = '#000'
            fill = '#fff'

            dx = station_direction['x1'] - x
            dy = station_direction['y1'] - y

            # The smaller dimension will be reset to 1
            width = abs(dx) + 1
            height = abs(dy) + 1

            # Can't rely on the line direction, because that only
            #   accounts for a single color
            if dx > 0 and dy == 0:
                line_direction = 'horizontal'
                height = 1
            elif dx == 0 and dy > 0:
                line_direction = 'vertical'
                width = 1
            elif dx > 0 and dy > 0:
                line_direction = 'diagonal-ne'
                width = 1
                # Diagonal stations look shorter, lengthen them
                height = lengthen_connecting_station(height)
            elif dx > 0 and dy < 0:
                line_direction = 'diagonal-ne'
                height = 1
                width = lengthen_connecting_station(width)

        elif station_direction == 'singleton':
            if line_direction != 'singleton' and not station.get('transfer'):
                width = 0.5

        if not draw_as_connected and shape == 'rect-round':
            radius = 0.125

        if line_direction == 'diagonal-ne':
            rotation = f'-45 {x} {y}'
        elif line_direction == 'diagonal-se':
            rotation = f'45 {x} {y}'
        else:
            rotation = False

        if not draw_as_connected and not transfer:
            if line_direction == 'vertical':
                width = 1
                y_offset = -0.25
            elif line_direction == 'horizontal':
                height = 1
                x_offset = -0.25
            elif line_direction == 'diagonal-se':
                height = 1
                x_offset = -0.25
            elif line_direction == 'diagonal-ne':
                height = 1
                x_offset = -0.25
            elif line_direction == 'singleton':
                width = 1
                height = 1

        if not draw_as_connected and shape == 'circles-thin':
            svg.append(svg_circle(x, y, .5, '#fff', '#000', stroke_width))
        else:
            svg.append(svg_rect(x, y, width, height, x_offset, y_offset, fill, stroke, stroke_width, radius, rotation))
    elif shape == 'circles-lg':
        if transfer:
            svg.append(svg_circle(x, y, 1.2, color))
            svg.append(svg_circle(x, y, .9, '#fff'))
        svg.append(svg_circle(x, y, .6, color))
        svg.append(svg_circle(x, y, .3, '#fff'))
        # Consider: Optimize into 1 call; non-xfer looks equivalent to <circle cx="53" cy="15" r="0.4" stroke="#ec2527" stroke-width="0.2" fill="#fff"/>
    elif shape == 'circles-md':
        if transfer and line_size >= 0.5:
            svg.append(svg_circle(x, y, .5, '#fff'))
            svg.append(svg_circle(x, y, .25, color))
        elif transfer:
            svg.append(svg_circle(x, y, .5, color))
        else:
            svg.append(svg_circle(x, y, .5, color))
            svg.append(svg_circle(x, y, .25, '#fff'))
    elif shape == 'circles-sm':
        if transfer and line_size >= 0.5:
            svg.append(svg_circle(x, y, .4, '#fff'))
            svg.append(svg_circle(x, y, .2, color))
        elif transfer:
            svg.append(svg_circle(x, y, .4, color))
        else:
            svg.append(svg_circle(x, y, .4, color))
            svg.append(svg_circle(x, y, .2, '#fff'))

    svg = ''.join(svg)

    return format_html(
        '{}',
        mark_safe(svg),
    )

def svg_circle(x, y, r, fill, stroke=None, stroke_width=0.5):
    if stroke:
        return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'

def svg_rect(x, y, w, h, x_offset, y_offset, fill, stroke=None, stroke_width=0.2, rx=None, rot=None):
    rx = f' rx="{rx}"' if rx else ''
    rot = f' transform="rotate({rot})"' if rot else ''
    if stroke:
        return f'<rect x="{x + x_offset}" y="{y + y_offset}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{rx}{rot}/>'
    return f'<rect x="{x + x_offset}" y="{y + y_offset}" width="{w}" height="{h}" fill="{fill}"{rx}{rot}/>'

def get_line_direction(x, y, color, points_by_color):

    """ Returns which direction this line is going in,
        to help draw the positioning of rectangle stations
    """

    color = color.removeprefix('#')

    NW = (x-1, y-1) in points_by_color[color]['xy']
    NE = (x+1, y-1) in points_by_color[color]['xy']
    SW = (x-1, y+1) in points_by_color[color]['xy']
    SE = (x+1, y+1) in points_by_color[color]['xy']
    N = (x, y-1) in points_by_color[color]['xy']
    E = (x+1, y) in points_by_color[color]['xy']
    S = (x, y+1) in points_by_color[color]['xy']
    W = (x-1, y) in points_by_color[color]['xy']

    if W and E:
        return 'horizontal'
    elif N and S:
        return 'vertical'
    elif NW and SE:
        return 'diagonal-se'
    elif SW and NE:
        return 'diagonal-ne'
    elif W or E:
        return 'horizontal'
    elif N or S:
        return 'vertical'
    elif NW or SE:
        return 'diagonal-se'
    elif SW or NE:
        return 'diagonal-ne'
    else:
        return 'singleton'

def get_connected_stations(x, y, stations):

    """ Returns connected stations along a SINGLE direction,
        with the goal of getting the xy coords of the ending connecting station
        for the direction with the longest connection.

        Alternatively, return:
            'conflicting' when more than one direction has an equal number of points,
            'singleton' if there are no adjacent stations,
            'internal' if this is an interior station and shouldn't be drawn
    """

    eligible_stations = [
        # Each station must be circles-thin, rect, or rect-round in order to qualify for connection
        (s['xy'][0], s['xy'][1]) for s in stations if s['style'] in ALLOWED_CONNECTING_STATIONS
    ]

    if (x, y) not in eligible_stations:
        return 'singleton'

    # I could set up a complex dictionary with coordinate offsets
    #   and avoid repeating myself several times,
    #   but I'm not convinced it would be more readable
    NW = (x-1, y-1) in eligible_stations
    NE = (x+1, y-1) in eligible_stations
    SW = (x-1, y+1) in eligible_stations
    SE = (x+1, y+1) in eligible_stations
    N = (x, y-1) in eligible_stations
    E = (x+1, y) in eligible_stations
    S = (x, y+1) in eligible_stations
    W = (x-1, y) in eligible_stations

    if not any([NW, NE, SW, SE, N, E, S, W]):
        return 'singleton'

    directions = 'N E S W NE SE SW NW'
    coords = {d: dict() for d in directions.split()}
    coords['highest'] = {d: 0 for d in directions.split()[:6]} # This slice/ordering looks wrong when compared to find_lines but it's OK
    coords['points'] = {d: set() for d in directions.split()[:6]}
    xn = x
    yn = y
    while E:
        coords['points']['E'].add((x, y))
        coords['points']['E'].add((xn, yn))
        xn += 1
        E = (xn, yn) in eligible_stations
        if not E:
            # End of the line!
            xn -= 1
            coords['E'] = {'x1': xn, 'y1': yn}
            break

    xn = x
    yn = y
    while S:
        coords['points']['S'].add((x, y))
        coords['points']['S'].add((xn, yn))
        yn += 1
        S = (xn, yn) in eligible_stations
        if not S:
            yn -= 1
            coords['S'] = {'x1': xn, 'y1': yn}
            break

    xn = x
    yn = y
    while NE:
        coords['points']['NE'].add((x, y))
        coords['points']['NE'].add((xn, yn))
        xn += 1
        yn -= 1
        NE = (xn, yn) in eligible_stations
        if not NE:
            xn -= 1
            yn += 1
            coords['NE'] = {'x1': xn, 'y1': yn}
            break

    xn = x
    yn = y
    while SE:
        coords['points']['SE'].add((x, y))
        coords['points']['SE'].add((xn, yn))
        xn += 1
        yn += 1
        SE = (xn, yn) in eligible_stations
        if not SE:
            xn -= 1
            yn -= 1
            coords['SE'] = {'x1': xn, 'y1': yn}
            break

    xn = x
    yn = y
    while W:
        coords['points']['E'].add((x, y))
        coords['points']['E'].add((xn, yn))
        xn -= 1
        W = (xn, yn) in eligible_stations
        if not W:
            xn += 1
            coords['E']['internal'] = True
            break

    xn = x
    yn = y
    while N:
        coords['points']['S'].add((x, y))
        coords['points']['S'].add((xn, yn))
        yn -= 1
        N = (xn, yn) in eligible_stations
        if not N:
            yn += 1
            coords['S']['internal'] = True
            break

    xn = x
    yn = y
    while NW:
        coords['points']['SE'].add((x, y))
        coords['points']['SE'].add((xn, yn))
        xn -= 1
        yn -= 1
        NW = (xn, yn) in eligible_stations
        if not NW:
            xn += 1
            yn += 1
            coords['SE']['internal'] = True
            break

    xn = x
    yn = y
    while SW:
        coords['points']['NE'].add((x, y))
        coords['points']['NE'].add((xn, yn))
        xn -= 1
        yn += 1
        SW = (xn, yn) in eligible_stations
        if not SW:
            xn += 1
            yn -= 1
            coords['NE']['internal'] = True
            break

    connections = [
        len(coords['points'][direction])
        for direction
        in coords['points']
    ]
    most_stations = max(connections)

    if connections.count(most_stations) > 1:
        return 'conflicting'

    for k,v in coords['points'].items():
        if len(v) == most_stations:
            longest = k
            break

    if coords[longest].get('internal'):
        return 'internal'

    return {
        'x1': coords[longest]['x1'],
        'y1': coords[longest]['y1'],
    }

def lengthen_connecting_station(length):

    """ Diagonal connecting stations look shorter,
        so lengthen them
    """

    if length <= 2:
        return length + 0.25
    elif length == 3:
        return length + 0.75
    else:
        return length + round((length - 2) / 2)

@register.simple_tag
def station_text(station):

    """ Generate the SVG text tag for a station based on
            whether it's a transfer station, and
            what its orientation is.

        Orientations where the text is on the left:
            text-anchor: "end" and x - .75 (or 1.5 for xfer)

        Confusingly, the station orientations given in the JSON data/HTML
            don't 100% translate here, because of slight differences
            in the SVG and HTML Canvas calculations.
            (That's why the station orientations are being re-written below.)
    """

    text_anchor = ''
    transform = ''

    name = station['name'].replace('_', ' ').strip()
    if not name:
        # Save a lot of KB by not including station names that won't be seen
        return ''

    assert isinstance(station['xy'][0], int)
    assert isinstance(station['xy'][1], int)
    assert station['orientation'] in ALLOWED_ORIENTATIONS

    if station.get('transfer'):
        x_val = station['xy'][0] + 1.5
    else:
        x_val = station['xy'][0] + 0.75

    if station['orientation'] == 0:
        # Right
        pass
    elif station['orientation'] in (
        45, # Below right, 45
        90, # Above, 90 -> SVG: (-90)
        -45, # Below right, 45
        ):
        if station['orientation'] == 90:
            station['orientation'] = -90

        transform = f' transform="rotate({station["orientation"]} {station["xy"][0]}, {station["xy"][1]})"'
    elif station['orientation'] in (
        180, # Left
        135, # Below left, 45 -> SVG: (-45)
        -135, # Above left, 45 -> SVG: (45)
        -90, # Below, 90
    ):
        text_anchor = ' text-anchor="end"'
        if station.get('transfer'):
            x_val = station['xy'][0] - 1.5
        else:
            x_val = station['xy'][0] - 0.75

        if station['orientation'] == 135:
            station['orientation'] = -45
        elif station['orientation'] == -135:
            station['orientation'] = 45

        if station['orientation'] == 180:
            transform = ''
        else:
            transform = f' transform="rotate({station["orientation"]} {station["xy"][0]}, {station["xy"][1]})"'

    text = f'''<text x="{x_val}" y="{station['xy'][1]}"{text_anchor}{transform}>'''

    return format_html(
        '{}{}{}',
        mark_safe(text),
        name,
        mark_safe('</text>'),
    )


@register.filter
def square_root(value):
    return sqrt(value)

@register.filter
def addf(value, arg):

    """ Like the built-in |add
        but allowing floats
    """

    try:
        return value + float(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except Exception:
            return ""

@register.filter
def static_cache_version(value):

    """ Automate generating a cache version string
        to bust the static cache
    """

    return getmtime(str(settings.BASE_DIR) + value)
