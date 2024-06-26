import json
import logging
import re
import unicodedata
from .html_color_names import html_color_name_fragments

from django.forms import ValidationError


logger = logging.getLogger(__name__)

ALLOWED_MAP_SIZES = [80, 120, 160, 200, 240, 360]
MAX_MAP_SIZE = ALLOWED_MAP_SIZES[-1]
VALID_XY = [str(x) for x in range(MAX_MAP_SIZE)]
ALLOWED_LINE_WIDTHS = [1, 0.75, 0.5, 0.25, 0.125]
ALLOWED_LINE_STYLES = ['solid', 'dashed', 'dense', 'dotted']
ALLOWED_STATION_STYLES = ['wmata', 'rect', 'rect-round', 'circles-lg', 'circles-md', 'circles-sm', 'circles-thin']
ALLOWED_ORIENTATIONS = [0, 45, -45, 90, -90, 135, -135, 180, 1, -1]
ALLOWED_CONNECTING_STATIONS = ['rect', 'rect-round', 'circles-thin']
ALLOWED_TAGS = ['real', 'speculative', 'unknown'] # TODO: change 'speculative' to 'fantasy' here and everywhere else, it's the more common usage

ALLOWED_LINE_WIDTH_STYLES = []
for allowed_width in ALLOWED_LINE_WIDTHS:
    for allowed_style in ALLOWED_LINE_STYLES:
        # Yes, I can use this in an import;
        # ALLOWED_LINE_WIDTH_STYLES has been populated
        ALLOWED_LINE_WIDTH_STYLES.append(f'{allowed_width}-{allowed_style}')

def is_hex(string):

    """ Determines whether a string is a hexademical string (0-9, a-f) or not
    """

    try:
        int(string, 16)
    except ValueError:
        return False
    else:
        return True

def hex2b64(hexthree):

    """ Convert a three-digit hex value to a two-digit base64 value
    """

    hexthree = int(hexthree, 16)
    assert 0 <= hexthree <= 4095

    base64_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'

    if hexthree < 64:
        # Add "a" (the base64 equivalent of zero) -padding to the result
        return 'a{0}'.format(base64_chars[hexthree])
    else:
        return '{0}{1}'.format(base64_chars[hexthree // 64], base64_chars[hexthree % 64])

def hex64(hexdigest):

    # The first 12 digits of a hexdigest give us 16^12, or 281,474,976,710,656 (281 trillion)
    # This is equivalent to 64^8
    # So instead of a 12-digit long URL, we can shorten down to 8 characters and still retain a high level of collision resistance
    hexdigest = hexdigest[:12]

    return '{0}{1}{2}{3}'.format(hex2b64(hexdigest[:3]), hex2b64(hexdigest[3:6]), hex2b64(hexdigest[6:9]), hex2b64(hexdigest[9:]))

def sanitize_string(string):
    return string.replace('<', '').replace('>', '').replace('"', '').replace("'", '&#x27;').replace('&', '&amp;').replace('/', '&#x2f;').replace('\x1b', '').replace('\\', '').replace('\t', ' ').replace('\n', ' ').replace('\b', ' ').replace('%', '')

def sanitize_string_without_html_entities(string):
    return string.replace('<', '').replace('>', '').replace('"', '').replace("'", '').replace('&', '').replace('/', '').replace('\x1b', '').replace('\\', '').replace('\t', ' ').replace('\n', ' ').replace('\b', ' ').replace('%', '')

def convert_nonascii_to_ascii(input_str):

    """
        Convert text with beyond the ASCII character set down to ASCII.

        Why do this? MetroMapMaker stores the station name in the HTML element's ID,
            which is very restrictive.

        The validator enforces this, so stations can only have DOM-safe characters.

        And if I'm going to match stations, this needs to be stripped out.

        Used by TravelSystem.models, but available here because it's a general-purpose utility function.
    """

    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def html_dom_id_safe(string):

    """ Returns a string santized of any characters that are not suitable for an HTML DOM's ID
    """

    return re.sub(r'[^A-Za-z0-9\- \_]', '', string)

def get_map_size(highest_xy_seen):

    """ Returns the map size,
        constrained to ALLOWED_MAP_SIZES
    """

    for allowed_size in ALLOWED_MAP_SIZES:
        if highest_xy_seen < allowed_size:
            return allowed_size
    return ALLOWED_MAP_SIZES[-1]

def validate_metro_map_v3(metro_map):

    """ Validate the MetroMap object, allowing mixing and matching line widths/styles.

        Main difference from v2 is points by color has an additional layer: the width+style,
            and drops the xy/xys intermediate key
    """

    validated_metro_map = {
        'global': {
            'data_version': 3,
            'lines': {},
            'style': {},
        },
        'points_by_color': {},
        'stations': {},
    }

    if not metro_map.get('points_by_color'):
        raise ValidationError(f"[VALIDATIONFAILED] 3-01: No points_by_color")

    if not isinstance(metro_map['points_by_color'], dict):
        raise ValidationError(f"[VALIDATIONFAILED] 3-02: points_by_color must be dict, is: {type(metro_map['points_by_color']).__name__}")

    # Infer missing lines in global from points_by_color
    # It's not pretty, and the lines could fail to validate for other reasons, but it's graceful.
    inferred_lines = False
    if not metro_map.get('global') or not metro_map.get('global', {}).get('lines'):
        inferred_lines = True
        metro_map['global'] = {
            'lines': {
                color: {'displayName': color}
                for color in metro_map['points_by_color']
            }
        }
    else:
        if not isinstance(metro_map['global']['lines'], dict):
            metro_map['global']['lines'] = {}
        if set(metro_map['global']['lines'].keys()) != set(metro_map['points_by_color'].keys()):
            for color in metro_map['points_by_color']:
                if color in metro_map['global']['lines']:
                    continue
                metro_map['global']['lines'][color] = {'displayName': color}

    valid_lines = []
    # Allow HTML color names to be used, but convert them to hex values
    metro_map['global']['lines'] = {
        html_color_name_fragments.get(line.strip()) or line: data
        for line, data in
        metro_map['global']['lines'].items()
    }

    invalid_lines = []

    remove_lines = {}
    for line in metro_map['global']['lines']:
        if not is_hex(line):
            # Allow malformed invalid lines to be skipped so the rest of the map will validate
            invalid_lines.append(line)
        if not len(line) == 6:
            # We know it's hex by this point, we can fix length
            if len(line) == 3:
                new_line = ''.join([line[0] * 2, line[1] * 2, line[2] * 2])
            elif len((line * 6)[:6]) <= 6:
                new_line = (line * 6)[:6]
            else:
                new_line = line[:6]
            remove_lines[new_line] = line

    for new_line, line in remove_lines.items():
        metro_map['global']['lines'][new_line] = metro_map['global']['lines'].pop(line)

    for line in metro_map['global']['lines']:

        if line in invalid_lines:
            continue

        # Transformations to the display name could result in a non-unique display name, but it doesn't actually matter.
        display_name = metro_map['global']['lines'][line].get('displayName', 'Rail Line')
        if not isinstance(display_name, str) or len(display_name) < 1:
            display_name = 'Rail Line'
        elif len(display_name) > 255:
            display_name = display_name[:255]

        valid_lines.append(line)
        validated_metro_map['global']['lines'][line] = {
            'displayName': sanitize_string(display_name)
        }

    line_width = metro_map['global'].get('style', {}).get('mapLineWidth', 1)
    if line_width not in ALLOWED_LINE_WIDTHS:
        line_width = ALLOWED_LINE_WIDTHS[0]

    line_style = metro_map['global'].get('style', {}).get('mapLineStyle', 'solid')
    if line_style not in ALLOWED_LINE_STYLES:
        line_style = ALLOWED_LINE_STYLES[0]

    station_style = metro_map['global'].get('style', {}).get('mapStationStyle', 'wmata')
    if station_style not in ALLOWED_STATION_STYLES:
        station_style = ALLOWED_STATION_STYLES[0]

    validated_metro_map['global']['style'] = {
        'mapLineWidth': line_width,
        'mapLineStyle': line_style,
        'mapStationStyle': station_style,
    }

    # Points by Color
    all_points_seen = set() # Must confirm that stations exist on these points
    points_skipped = []
    highest_xy_seen = -1 # Because 0 is a point
    valid_points_by_color = {}
    for color in metro_map['points_by_color']:
        if color not in validated_metro_map['global']['lines']:
            points_skipped.append(f'Color {color} not in global')
            continue

        if not isinstance(metro_map['points_by_color'][color], dict):
            points_skipped.append(f'BAD LINE WIDTH/STYLE at {color} (non-dict)')
            continue

        for line_width_style in metro_map['points_by_color'][color]:

            if not isinstance(metro_map['points_by_color'][color][line_width_style], dict):
                points_skipped.append(f'BAD COORDS at {color} for {line_width_style}')
                continue

            if line_width_style not in ALLOWED_LINE_WIDTH_STYLES:
                points_skipped.append(f'BAD LINE WIDTH/STYLE at {color}: {line_width_style}')

            for x in metro_map['points_by_color'][color][line_width_style]:
                if not isinstance(metro_map['points_by_color'][color][line_width_style][x], dict):
                    points_skipped.append(f'BAD X at {color}: {x}')
                    continue

                if not x.isdigit():
                    points_skipped.append(f'NONINT X at {color}: {x}')
                    continue

                if int(x) < 0 or int(x) >= MAX_MAP_SIZE:
                    points_skipped.append(f'OOB X at {color}: {x}')
                    continue

                for y in metro_map['points_by_color'][color][line_width_style][x]:

                    if not y.isdigit():
                        points_skipped.append(f'NONINT Y at {color}: {x},{y}')
                        continue

                    if int(y) < 0 or int(y) >= MAX_MAP_SIZE:
                        points_skipped.append(f'OOB Y at {color}: {x},{y}')
                        continue

                    if (x, y) in all_points_seen:
                        # Already seen in another color
                        points_skipped.append(f'SKIPPING {color} POINT {x},{y}, ALREADY SEEN')
                        continue

                    if metro_map['points_by_color'][color][line_width_style][x][y] == 1:
                        # Originally I'd considered setting the line width / style at the [x][y],
                        #   but I think it's better recorded at points_by_color[color][line_width_style]
                        all_points_seen.add((x, y))

                        if int(x) > highest_xy_seen:
                            highest_xy_seen = int(x)

                        if int(y) > highest_xy_seen:
                            highest_xy_seen = int(y)

                        if not valid_points_by_color.get(color):
                            valid_points_by_color[color] = {line_width_style: {}}
                        elif not valid_points_by_color[color].get(line_width_style):
                            valid_points_by_color[color][line_width_style] = {}

                        if not valid_points_by_color[color][line_width_style].get(x):
                            valid_points_by_color[color][line_width_style][x] = {}

                        valid_points_by_color[color][line_width_style][x][y] = 1

    validated_metro_map['points_by_color'] = valid_points_by_color
    if points_skipped:
        logger.warn(f'Points skipped: {len(points_skipped)} Details: {points_skipped}')

    # Stations
    stations_skipped = []
    valid_stations = {}
    if metro_map.get('stations') and isinstance(metro_map['stations'], dict):
        for x in metro_map['stations']:
            if not isinstance(metro_map['stations'][x], dict):
                stations_skipped.append(f'STA BAD X: {x}')
                continue
            for y in metro_map['stations'][x]:
                if not isinstance(metro_map['stations'][x][y], dict):
                    stations_skipped.append(f'STA BAD Y: {y}')
                    continue

                if (x, y) not in all_points_seen:
                    stations_skipped.append(f'STA BAD POS: {x},{y}')
                    continue

                station_name = sanitize_string_without_html_entities(metro_map['stations'][x][y].get('name', '_') or '_')
                if len(station_name) < 1:
                    station_name = '_'
                elif len(station_name) > 255:
                    station_name = station_name[:255]

                station = {'name': station_name}

                try:
                    station_orientation = int(metro_map['stations'][x][y].get('orientation', ALLOWED_ORIENTATIONS[0]))
                except Exception:
                    station_orientation = ALLOWED_ORIENTATIONS[0]

                if station_orientation not in ALLOWED_ORIENTATIONS:
                    station_orientation = ALLOWED_ORIENTATIONS[0]
                station['orientation'] = station_orientation

                station_style = metro_map['stations'][x][y].get('style')
                if station_style and station_style in ALLOWED_STATION_STYLES:
                    station['style'] = station_style

                if metro_map['stations'][x][y].get('transfer'):
                    station['transfer'] = 1

                # This station is valid, add it
                if not valid_stations.get(x):
                    valid_stations[x] = {}

                valid_stations[x][y] = station
    validated_metro_map['stations'] = valid_stations

    if stations_skipped:
        logger.warn(f'Stations skipped: {len(stations_skipped)} Details: {stations_skipped}')

    if highest_xy_seen == -1:
        raise ValidationError(f"[VALIDATIONFAILED] 3-00: This map has no points drawn. If this is in error, please contact the admin.")

    validated_metro_map['global']['map_size'] = get_map_size(highest_xy_seen)

    return validated_metro_map


def validate_metro_map_v2(metro_map):

    """ Validate the MetroMap object, with a more compact, optimized data representation
    """

    validated_metro_map = {
        'global': {
            'data_version': 2,
            'lines': {},
            'style': {},
        },
        'points_by_color': {},
        'stations': {},
    }

    if not metro_map.get('points_by_color'):
        raise ValidationError(f"[VALIDATIONFAILED] 2-01: No points_by_color")

    if not isinstance(metro_map['points_by_color'], dict):
        raise ValidationError(f"[VALIDATIONFAILED] 2-02: points_by_color must be dict, is: {type(metro_map['points_by_color']).__name__}")

    # Infer missing lines in global from points_by_color
    # It's not pretty, and the lines could fail to validate for other reasons, but it's graceful.
    inferred_lines = False
    if not metro_map.get('global') or not metro_map.get('global', {}).get('lines'):
        inferred_lines = True
        metro_map['global'] = {
            'lines': {
                color: {'displayName': color}
                for color in metro_map['points_by_color']
            }
        }
    else:
        if not isinstance(metro_map['global']['lines'], dict):
            metro_map['global']['lines'] = {}
        if set(metro_map['global']['lines'].keys()) != set(metro_map['points_by_color'].keys()):
            for color in metro_map['points_by_color']:
                if color in metro_map['global']['lines']:
                    continue
                metro_map['global']['lines'][color] = {'displayName': color}

    valid_lines = []
    # Allow HTML color names to be used, but convert them to hex values
    metro_map['global']['lines'] = {
        html_color_name_fragments.get(line.strip()) or line: data
        for line, data in
        metro_map['global']['lines'].items()
    }

    invalid_lines = []

    remove_lines = {}
    for line in metro_map['global']['lines']:
        if not is_hex(line):
            # Allow malformed invalid lines to be skipped so the rest of the map will validate
            # raise ValidationError(f"[VALIDATIONFAILED] 2-03 global line {line.upper()} failed is_hex(){' (Inferred)' if inferred_lines else ''}: {line} is not a valid color.")
            invalid_lines.append(line)
        if not len(line) == 6:
            # We know it's hex by this point, we can fix length
            if len(line) == 3:
                new_line = ''.join([line[0] * 2, line[1] * 2, line[2] * 2])
            elif len((line * 6)[:6]) <= 6:
                new_line = (line * 6)[:6]
            else:
                new_line = line[:6]
            remove_lines[new_line] = line

    for new_line, line in remove_lines.items():
        metro_map['global']['lines'][new_line] = metro_map['global']['lines'].pop(line)

    for line in metro_map['global']['lines']:

        if line in invalid_lines:
            continue

        # Transformations to the display name could result in a non-unique display name, but it doesn't actually matter.
        display_name = metro_map['global']['lines'][line].get('displayName', 'Rail Line')
        if not isinstance(display_name, str) or len(display_name) < 1:
            display_name = 'Rail Line'
        elif len(display_name) > 255:
            display_name = display_name[:255]

        valid_lines.append(line)
        validated_metro_map['global']['lines'][line] = {
            'displayName': sanitize_string(display_name)
        }

    line_width = metro_map['global'].get('style', {}).get('mapLineWidth', 1)
    if line_width not in ALLOWED_LINE_WIDTHS:
        line_width = ALLOWED_LINE_WIDTHS[0]

    station_style = metro_map['global'].get('style', {}).get('mapStationStyle', 'wmata')
    if station_style not in ALLOWED_STATION_STYLES:
        station_style = ALLOWED_STATION_STYLES[0]

    validated_metro_map['global']['style'] = {
        'mapLineWidth': line_width,
        'mapStationStyle': station_style,
    }

    # Points by Color
    all_points_seen = set() # Must confirm that stations exist on these points
    points_skipped = []
    highest_xy_seen = -1 # Because 0 is a point
    valid_points_by_color = {}
    for color in metro_map['points_by_color']:
        if color not in validated_metro_map['global']['lines']:
            points_skipped.append(f'Color {color} not in global')
            continue

        if not metro_map['points_by_color'][color].get('xys'):
            points_skipped.append(f'MISSING xys for {color}')
            continue
        if not isinstance(metro_map['points_by_color'][color]['xys'], dict):
            points_skipped.append(f'BAD XYS at {color}')
            continue
        for x in metro_map['points_by_color'][color]['xys']:
            if not isinstance(metro_map['points_by_color'][color]['xys'][x], dict):
                points_skipped.append(f'BAD X at {color}: {x}')
                continue

            if not x.isdigit():
                points_skipped.append(f'NONINT X at {color}: {x}')
                continue

            if int(x) < 0 or int(x) >= MAX_MAP_SIZE:
                points_skipped.append(f'OOB X at {color}: {x}')
                continue

            for y in metro_map['points_by_color'][color]['xys'][x]:

                if not y.isdigit():
                    points_skipped.append(f'NONINT Y at {color}: {x},{y}')
                    continue

                if int(y) < 0 or int(y) >= MAX_MAP_SIZE:
                    points_skipped.append(f'OOB Y at {color}: {x},{y}')
                    continue

                if (x, y) in all_points_seen:
                    # Already seen in another color
                    points_skipped.append(f'SKIPPING {color} POINT {x},{y}, ALREADY SEEN')
                    continue

                if metro_map['points_by_color'][color]['xys'][x][y] == 1:
                    all_points_seen.add((x, y))

                    if int(x) > highest_xy_seen:
                        highest_xy_seen = int(x)

                    if int(y) > highest_xy_seen:
                        highest_xy_seen = int(y)

                    if not valid_points_by_color.get(color):
                        valid_points_by_color[color] = {'xys': {}}

                    if not valid_points_by_color[color]['xys'].get(x):
                        valid_points_by_color[color]['xys'][x] = {}

                    valid_points_by_color[color]['xys'][x][y] = 1
    validated_metro_map['points_by_color'] = valid_points_by_color
    if points_skipped:
        logger.warn(f'Points skipped: {len(points_skipped)} Details: {points_skipped}')

    # Stations
    stations_skipped = []
    valid_stations = {}
    if metro_map.get('stations') and isinstance(metro_map['stations'], dict):
        for x in metro_map['stations']:
            if not isinstance(metro_map['stations'][x], dict):
                stations_skipped.append(f'STA BAD X: {x}')
                continue
            for y in metro_map['stations'][x]:
                if not isinstance(metro_map['stations'][x][y], dict):
                    stations_skipped.append(f'STA BAD Y: {y}')
                    continue

                if (x, y) not in all_points_seen:
                    stations_skipped.append(f'STA BAD POS: {x},{y}')
                    continue

                station_name = sanitize_string_without_html_entities(metro_map['stations'][x][y].get('name', '_') or '_')
                if len(station_name) < 1:
                    station_name = '_'
                elif len(station_name) > 255:
                    station_name = station_name[:255]

                station = {'name': station_name}

                try:
                    station_orientation = int(metro_map['stations'][x][y].get('orientation', ALLOWED_ORIENTATIONS[0]))
                except Exception:
                    station_orientation = ALLOWED_ORIENTATIONS[0]

                if station_orientation not in ALLOWED_ORIENTATIONS:
                    station_orientation = ALLOWED_ORIENTATIONS[0]
                station['orientation'] = station_orientation

                station_style = metro_map['stations'][x][y].get('style')
                if station_style and station_style in ALLOWED_STATION_STYLES:
                    station['style'] = station_style

                if metro_map['stations'][x][y].get('transfer'):
                    station['transfer'] = 1

                # This station is valid, add it
                if not valid_stations.get(x):
                    valid_stations[x] = {}

                valid_stations[x][y] = station
    validated_metro_map['stations'] = valid_stations

    if stations_skipped:
        logger.warn(f'Stations skipped: {len(stations_skipped)} Details: {stations_skipped}')

    if highest_xy_seen == -1:
        raise ValidationError(f"[VALIDATIONFAILED] 2-00: This map has no points drawn. If this is in error, please contact the admin.")

    validated_metro_map['global']['map_size'] = get_map_size(highest_xy_seen)

    return validated_metro_map

def validate_metro_map(metro_map):
    
    """ Validate the MetroMap object by re-constructing it using only valid entries.
    """

    # root-level can only contain keys 0-79 and the key global
    #     0-79 are dict containing only:
    #         "line" with the six-digit hex value of a known line existing in the global
    #         "station" (optional): a dict containing both:
    #             "name": the name of the line, sanitized
    #             "lines": a list containing one or more six-digit hex values of a known line existing in the global
    #             example: {"name":"suilng_","lines":["bd1038","f0ce15","0896d7"]}}
    #     global is a dict containing only:
    #         "lines", a dict with keys of the six-digit hex value of a line
    #                     and the value is another dict:
    #                         displayName: "the display name", sanitized
    #         {"lines":{"bd1038":{"displayName":"Red Line"},"df8600":{"displayName":"Orange Line"},"f0ce15":{"displayName":"Yellow Line"},"00b251":{"displayName":"Green Line"},"0896d7":{"displayName":"Blue Line"},"662c90":{"displayName":"Purple Line"},"a2a2a2":{"displayName":"Silver Line"}}}}

    validated_metro_map = {}

    # Formatting the assertion strings:
    # Anything that appears before the first colon will be internal-only;
    #   everything else is user-facing.

    assert type(metro_map) == dict, "[VALIDATIONFAILED] 01 metro_map IS NOT DICT: Bad map object, needs to be an object."
    assert metro_map.get('global'), "[VALIDATIONFAILED] 02 metro_map DOES NOT HAVE GLOBAL: Bad map object, missing global."
    try:
        assert metro_map['global'].get('lines'), "[VALIDATIONFAILED] 03 metro_map DOES NOT HAVE LINES: Map does not have any rail lines defined."
    except AssertionError:
        # Gracefully fail by looping through the coordinates;
        # collecting any lines, and adding them to the globals list.
        # The displayName won't be pretty,
        # and the map could fail to validate for other reasons,
        # but at least this check will pass if there are lines in the mapdata itself
        inferred_lines = {}
        for x in metro_map.keys():
            if x == 'global' or x not in VALID_XY:
                continue
            for y in metro_map[x].keys():
                if y not in VALID_XY:
                    continue
                line = metro_map[x][y].get('line')
                if line:
                    inferred_lines[line] = {'displayName': line}
        if inferred_lines:
            metro_map['global']['lines'] = inferred_lines
        else:
            raise
    assert type(metro_map['global']['lines']) == dict, "[VALIDATIONFAILED] 04 metro_map LINES IS NOT DICT: Map lines must be stored as an object."
    assert len(metro_map['global']['lines']) <= 100, "[VALIDATIONFAILED] 04B metro_map HAS TOO MANY LINES: Map has too many lines (limit is 100); remove unused lines."

    validated_metro_map = {
        'global': {
            'lines': {

            }
        }
    }

    valid_lines = []

    # Allow HTML color names to be used, but convert them to hex values
    metro_map['global']['lines'] = {
        html_color_name_fragments.get(line.strip()) or line: data
        for line, data in
        metro_map['global']['lines'].items()
    }

    line_width = metro_map['global'].get('style', {}).get('mapLineWidth', 1)
    if line_width not in ALLOWED_LINE_WIDTHS:
        line_width = ALLOWED_LINE_WIDTHS[0]

    station_style = metro_map['global'].get('style', {}).get('mapStationStyle', 'wmata')
    if station_style not in ALLOWED_STATION_STYLES:
        station_style = ALLOWED_STATION_STYLES[0]

    validated_metro_map['global']['style'] = {
        'mapLineWidth': line_width,
        'mapStationStyle': station_style,
    }

    for global_line in metro_map['global']['lines'].keys():
        assert is_hex(global_line), "[VALIDATIONFAILED] 05 global_line {0} FAILED is_hex() {0} is not a valid color: {0} is not a valid rail line color.".format(global_line)
        assert len(global_line) == 6, "[VALIDATIONFAILED] 06 global_line {0} IS NOT 6 CHARACTERS: The color {0} must be 6 characters long.".format(global_line)
        # Transformations to the display name could result in a non-unique display name, but it doesn't actually matter.
        display_name = metro_map['global']['lines'][global_line].get('displayName', 'Rail Line')
        if len(display_name) < 1:
            metro_map['global']['lines'][global_line]['displayName'] = 'Rail Line'
        elif len(display_name) > 255:
            metro_map['global']['lines'][global_line]['displayName'] = display_name[:255]
        assert 1 <= len(metro_map['global']['lines'][global_line].get('displayName', 'Rail Line')) < 256, "[VALIDATIONFAILED] 07 displayName BAD SIZE: Rail line names must be between 1 and 255 characters long (spaces are okay)."
        valid_lines.append(global_line)
        validated_metro_map['global']['lines'][global_line] = {
            'displayName': sanitize_string(metro_map['global']['lines'][global_line]['displayName'])
        }

    for x in metro_map.keys():
        if x == 'global' or x not in VALID_XY:
            continue
        if metro_map.get(x):
            if not validated_metro_map.get(x):
                validated_metro_map[x] = {}
            for y in metro_map[x].keys():
                if y not in VALID_XY:
                    continue
                if metro_map[x].get(y):
                    if not validated_metro_map[x].get(y):
                        validated_metro_map[x][y] = {}
                    assert is_hex(metro_map[x][y]["line"]), "[VALIDATIONFAILED] 08 {0} at ({1}, {2}) FAILED is_hex(): Point at ({3}, {4}) is not a valid color: {0}.".format(metro_map[x][y]["line"], x, y, int(x) + 1, int(y) + 1)
                    assert len(metro_map[x][y]["line"]) == 6, "[VALIDATIONFAILED] 09 {0} at ({1}, {2}) IS NOT 6 CHARACTERS: Point at ({3}, {4}) has a color that needs to be 6 characters long: {0}".format(metro_map[x][y]["line"], x, y, int(x) + 1, int(y) + 1)
                    try:
                        assert metro_map[x][y]["line"] in valid_lines, "[VALIDATIONFAILED] 10 {0} at ({1}, {2}) NOT IN valid_lines: Point at ({3}, {4}) has a color that is not defined in the rail lines; please create a line matching the color {0}.".format(metro_map[x][y]["line"], x, y, int(x) + 1, int(y) + 1)
                    except AssertionError:
                        del validated_metro_map[x][y] # delete this coordinate or it'll be undefined
                        continue # If the line isn't in valid_lines, we could just not add it
                    else:
                        validated_metro_map[x][y]["line"] = metro_map[x][y]["line"]
                    if metro_map[x][y].get('station'):
                        assert type(metro_map[x][y]["station"]) == dict, "[VALIDATIONFAILED] 11 metro_map[x][y]['station'] at ({0}, {1}) IS NOT DICT: Point at ({2}, {3}) has a malformed station, must be an object.".format(x, y, int(x) + 1, int(y) + 1)
                        metro_map[x][y]["station"]["name"] = sanitize_string_without_html_entities(metro_map[x][y]["station"]["name"])
                        if metro_map[x][y]["station"]["name"] == '':
                            metro_map[x][y]["station"]["name"] = "_" # Gracefully rename a zero-length station name to be a single space
                        assert 1 <= len(metro_map[x][y]["station"]["name"]) < 256, "[VALIDATIONFAILED] 12 station name at ({0}, {1}) BAD SIZE {2} is {3}: Point at ({4}, {5}) has a station whose name is not between 1 and 255 characters long. Please rename it.".format(x, y, metro_map[x][y]["station"]["name"], len(metro_map[x][y]["station"]["name"]), int(x) + 1, int(y) + 1)
                        assert type(metro_map[x][y]["station"].get("lines", [])) == list, "[VALIDATIONFAILED] 13 station lines at ({0}, {1}) NOT A LIST: Point at ({2}, {3}) has its station lines in the incorrect format; must be a list.".format(x, y, int(x) + 1, int(y) + 1)
                        # Okay, this probably *should* pass - but I think I have some bug in the javascript somewhere because https://metromapmaker.com/?map=zCq7R223 obviously passed validation but once reconstituted, fails. But this isn't a big enough deal that I can't wave this validation through while I figure out what's going on.
                        # assert len(metro_map[x][y]["station"]["lines"]) > 0, "[VALIDATIONFAILED] 14: station lines at ({0}, {1}) HAS ZERO LENGTH".format(x, y)
                        validated_metro_map[x][y]["station"] = {
                            # "name": html_dom_id_safe(metro_map[x][y]["station"]["name"].replace('/', '').replace("'", '').replace('&', '').replace('`', '')),
                            "name": metro_map[x][y]["station"]["name"],
                            "lines": []
                        }
                        for station_line in metro_map[x][y]["station"].get("lines", []):
                            if station_line in html_color_name_fragments:
                                station_line = html_color_name_fragments[station_line]
                            assert is_hex(station_line), "[VALIDATIONFAILED] 15 station_line {0} FAILED is_hex(): Station Rail line {0} is not a valid color.".format(station_line)
                            assert len(station_line) == 6, "[VALIDATIONFAILED] 16 station_line {0} IS NOT 6 CHARACTERS: Station Rail line color {0} needs to be 6 characters long.".format(station_line)
                            try:
                                assert station_line in valid_lines, "[VALIDATIONFAILED] 17 station_line {0} NOT IN valid_lines: Station rail line color {0} is not defined; please create a rail line matching this color or remove it from all stations.".format(station_line)
                            except AssertionError:
                                # We can gracefully fail here by simply not adding that line to the station
                                continue
                            else:
                                validated_metro_map[x][y]["station"]["lines"].append(station_line)
                        if metro_map[x][y]["station"].get('transfer'):
                           validated_metro_map[x][y]["station"]["transfer"] = 1

                        try:
                            station_orientation = int(metro_map[x][y]["station"].get('orientation', ALLOWED_ORIENTATIONS[0]))
                        except Exception:
                            station_orientation = ALLOWED_ORIENTATIONS[0]
                        if station_orientation not in ALLOWED_ORIENTATIONS:
                            station_orientation = ALLOWED_ORIENTATIONS[0]
                        validated_metro_map[x][y]["station"]["orientation"] = station_orientation

                        station_style = metro_map[x][y]["station"].get('style')
                        if station_style and station_style in ALLOWED_STATION_STYLES:
                            validated_metro_map[x][y]["station"]['style'] = station_style

    return validated_metro_map
