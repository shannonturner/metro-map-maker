from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from math import sqrt

register = template.Library()

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

    if station['transfer']:
        x_val = station['xy'][0] + 1.5
    else:
        x_val = station['xy'][0] + 0.75

    if station['orientation'] == 0:
        # Right
        pass
    elif station['orientation'] in (
        '45', # Below right, 45
        '90', # Above, 90 -> SVG: (-90)
        '-45', # Below right, 45
        ):
        if station['orientation'] == '90':
            station['orientation'] = '-90' 

        transform = f'transform="rotate({station["orientation"]} {station["xy"][0]}, {station["xy"][1]})"'
    elif station['orientation'] in (
        '180', # Left
        '135', # Below left, 45 -> SVG: (-45)
        '-135', # Above left, 45 -> SVG: (45)
        '-90', # Below, 90
    ):
        text_anchor = 'text-anchor="end"'
        if station['transfer']:
            x_val = station['xy'][0] - 1.5
        else:
            x_val = station['xy'][0] - 0.75

        if station['orientation'] == '135':
            station['orientation'] = '-45'
        elif station['orientation'] == '-135':
            station['orientation'] = '45'

        if station['orientation'] == '180':
            transform = ''
        else:
            transform = f'transform="rotate({station["orientation"]} {station["xy"][0]}, {station["xy"][1]})"'

    name = station['name'].replace('_', ' ')
    text = f'''<text dominant-baseline="central" x="{x_val}" y="{station['xy'][1]}" {text_anchor} {transform}>'''

    return format_html(
        '{}{}{}',
        mark_safe(text),
        name,
        mark_safe('</text>'),
    )


@register.filter
def square_root(value):
    return sqrt(value)
