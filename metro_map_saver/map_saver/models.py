from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from django.db import models

from citysuggester.utils import suggest_city
from taggit.managers import TaggableManager

import datetime
import json
import subprocess
import time


PUBLICLY_VISIBLE_TAGS = [
    'real',
    'speculative',
    'unknown',
]

# Having any of these tags excludes you from public visibility
EXCLUDED_TAGS = [
    'reviewed',
    'excluded',
]

def get_thumbnail_filepath(instance, original):
    thousand = instance.pk // 1000
    if original.endswith('svg'):
        ftype = 'svg'
    elif original.endswith('png'):
        ftype = 'png'
    else:
        raise NotImplementedError('Invalid filetype')
    filename = f'{instance.urlhash}.{ftype}'
    return f'thumbnails/{str(thousand)}/{filename}'

def get_image_filepath(instance, original):
    thousand = instance.pk // 1000
    if original.endswith('svg'):
        ftype = 'svg'
    elif original.endswith('png'):
        ftype = 'png'
    else:
        raise NotImplementedError('Invalid filetype')
    filename = f'{instance.urlhash}.{ftype}'
    return f'images/{str(thousand)}/{filename}'

class SavedMap(models.Model):

    """ Saves map data and its corresponding urlhash together so that maps can be easily shared
    """

    urlhash = models.CharField(max_length=8)
    mapdata = models.TextField(blank=True) # Consider: Delete after migration to v2 representation
    # v2+ representation of map data
    data = models.JSONField(default=dict, blank=True)
    # gallery_visible: should this be shown in the default view of the Admin Gallery?
    gallery_visible = models.BooleanField(default=True)
    # publicly_visible: should this be shown in the publicly-visible gallery?
    #   (using this to improve speed and reduce query complexity)
    publicly_visible = models.BooleanField(default=False)
    name = models.CharField(max_length=255, blank=True, default='', help_text='User-provided (or admin-provided) name for a map. When user-provided, contains tags like (real).')
    thumbnail = models.TextField(blank=True, default='') # Consider: Delete after thumbnail files generation migration
    thumbnail_svg = models.FileField(upload_to=get_thumbnail_filepath, null=True, blank=True)
    thumbnail_png = models.FileField(upload_to=get_thumbnail_filepath, null=True, blank=True)
    svg = models.FileField(upload_to=get_image_filepath, null=True, blank=True)
    png = models.FileField(upload_to=get_image_filepath, null=True, blank=True)
    stations = models.TextField(blank=True, default='')
    station_count = models.IntegerField(default=-1)
    created_at = models.DateTimeField(auto_now_add=True)

    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    # Create a token that can be used for creators to be able to name their maps
    # but subsequent visitors to that map will not be able to rename it
    naming_token = models.CharField(max_length=64, blank=True, default='')

    # Store the suggested city (if any) so we can refer to it
    # without needing to calculate it every time
    # Consider: making suggested_city a foreign key to TravelSystem
    #   this would also mean that renaming a TravelSystem wouldn't
    #   require re-saving maps with that suggested_city to prevent 500 errors in the admin
    #   (though I don't re-name TravelSystems often)
    suggested_city = models.CharField(max_length=255, blank=True, default='', help_text='Suggested name for this map based on station name overlap with real, existing Metro systems.')
    suggested_city_overlap = models.IntegerField(default=-1)

    map_size = models.IntegerField(default=-1)

    city = models.ForeignKey(
        'City',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='The city (location) this map refers to. Differs from name and suggested_city by being the standard, canonical name of a city.',
    )


    tags = TaggableManager(blank=True)

    def _suggest_city(self, overlap=None):

        """ Override overlap to specify the number of stations
            that must overlap to be considered a match;
            uses utils.MINIMUM_STATION_OVERLAP otherwise
        """

        return suggest_city(set(self.stations.lower().split(',')), overlap)

    def _get_stations(self):

        """ Returns a set of station names from a given mapdata
        """

        stations = set()

        if self.data:
            for x in self.data.get('stations', {}):
                for y in self.data['stations'][x]:
                    stations.add(self.data['stations'][x][y].get('name', '').lower())
            return ','.join(stations)
        elif self.mapdata:
            try:
                mapdata = json.loads(self.mapdata)
            except Exception:
                return ''

            for x in mapdata:
                for y in mapdata[x]:
                    if 'station' in mapdata[x][y]:
                        stations.add(mapdata[x][y]['station'].get('name', '').lower())
            return ','.join(stations)
        else:
            return ''

    def _station_count(self):
        if self.stations:
            return self.stations.count(',')
        else:
            return 0

    def convert_mapdata_v1_to_v2(self):

        """ Convert mapdata (classic) from v1 to v2
        """

        from .mapdata_optimizer import sort_points_by_color

        try:
            mapdata = json.loads(self.mapdata)
        except json.decoder.JSONDecodeError as exc:
            raise

        if mapdata['global'].get('data_version', 1) > 1:
            raise ValueError('This map is not data_version v1; cannot convert to v2')

        # Note that sort_points_by_color is NOT the reduced set of points, which is good here
        points_by_color, stations, map_size = sort_points_by_color(mapdata, map_type='classic', data_version=1)

        mapdata_v2 = {
            'global': {
                'data_version': 2,
                'map_size': map_size,
                'lines': mapdata['global']['lines'],
            },
            'stations': stations,
            'points_by_color': points_by_color,
        }

        style = mapdata['global'].get('style')
        if style:
            mapdata_v2['global']['style'] = style

        # Think I'm going to drop this feature after all; it's more clutter than helpful
        for index, station in enumerate(mapdata_v2['stations']):
            mapdata_v2['stations'][index].pop('lines', None)

        self.data = self.data_optimized_for_js_performance(mapdata_v2)
        self.save()

    def data_optimized_for_js_performance(self, mapdata_v2):

        """ sort_points_by_color is a good midway point between being optimized for
                data size / SVG generation (Python)
                loading speed (Javascript performance)

            For instance, having 
                mapdata_v2['points_by_color'][color]['x'] and
                mapdata_v2['points_by_color'][color]['y']

                in the Javascript is not useful, but can be very useful when drawing an SVG
                    to minimize the number of points in a polyline and determining squares

            On the other end,
                mapdata_v2['points_by_color'][color]['xy'] being a list of 2-tuple coordinate points
                    is a very info-dense, non-lossy representation of the data,
                    but in Javascript is VERY slow to look up whether a given point is adjacent
                    to a known point.

                The fastest lookup I've tested is still checking map[x] && map[x][y].

            Similarly, for SVGs it's fine that stations is a list of dicts,
                but doing a lookup on a list isn't great. Again, use [x] && [x][y] pattern.

            In short: the JS side needs to be as performant as possible,
                so store the optimized data in .data

            We can afford to re-run .sort_points_by_color to generate the SVG,
                which is done less frequently than accessing the JS
                (and ideally only once)
        """

        for color in mapdata_v2['points_by_color']:
            mapdata_v2['points_by_color'][color].pop('x', None)
            mapdata_v2['points_by_color'][color].pop('y', None)

            mapdata_v2['points_by_color'][color]['xys'] = {}
            for xy in mapdata_v2['points_by_color'][color]['xy']:
                x, y = xy
                if x not in mapdata_v2['points_by_color'][color]['xys']:
                    mapdata_v2['points_by_color'][color]['xys'][x] = {}
                mapdata_v2['points_by_color'][color]['xys'][x][y] = 1
            del mapdata_v2['points_by_color'][color]['xy']

        stations = {}
        for station in mapdata_v2['stations']:
            x, y = station['xy']
            if not stations.get(x):
                stations[x] = {}
            stations[x][y] = station
            stations[x][y].pop('xy')
            stations[x][y].pop('color')
        mapdata_v2['stations'] = stations

        return mapdata_v2

    def generate_images(self):

        """ Generates full-size images and thumbnails
                (PNG and SVG for both)
        """

        from .mapdata_optimizer import (
            add_stations_to_svg,
            find_lines,
            sort_points_by_color,
            get_svg_from_shapes_by_color,
        )

        t0 = time.time()

        mapdata = self.data or json.loads(self.mapdata)
        data_version = mapdata['global'].get('data_version', 1)

        if mapdata['global'].get('style'):
            line_size = mapdata['global']['style'].get('mapLineWidth', 1)
            default_station_shape = mapdata['global']['style'].get('mapStationStyle', 'wmata')
        else:
            line_size = 1
            default_station_shape = 'wmata'

        points_by_color, stations, map_size = sort_points_by_color(mapdata, data_version=data_version)
        shapes_by_color = {}
        for color in points_by_color:
            points_this_color = points_by_color[color]['xy']

            lines, singletons = find_lines(points_this_color)
            shapes_by_color[color] = {'lines': lines, 'points': singletons}

        thumbnail_svg = get_svg_from_shapes_by_color(shapes_by_color, map_size, line_size, default_station_shape, points_by_color, stations)

        thumbnail_svg_file = ContentFile(thumbnail_svg, name=f"t{self.urlhash}.svg")
        self.thumbnail_svg = thumbnail_svg_file

        svg = add_stations_to_svg(thumbnail_svg, line_size, default_station_shape, points_by_color, stations)
        svg_file = ContentFile(svg, name=f"{self.urlhash}.svg")
        self.svg = svg_file
        self.save()

        t1 = time.time()

        thumbnail_png_filename = self.thumbnail_svg.path.removesuffix('.svg') + '.png'
        png_filename = self.svg.path.removesuffix('.svg') + '.png'

        subprocess.run([settings.PNG_CONVERSION_APP_PATH, *settings.PNG_CONVERSION_ARGS_THUMBNAIL, thumbnail_png_filename, self.thumbnail_svg.path], capture_output=True)

        subprocess.run([settings.PNG_CONVERSION_APP_PATH, *settings.PNG_CONVERSION_ARGS, png_filename, self.svg.path], capture_output=True)

        self.thumbnail_png = thumbnail_png_filename.removeprefix(settings.MEDIA_ROOT)
        self.png = png_filename.removeprefix(settings.MEDIA_ROOT)
        self.save()

        t2 = time.time()

        # These report the same time, but the station generation is negligible
        now = datetime.datetime.now().replace(microsecond=0)
        output = f'[{now}] Wrote images for #{self.pk} ({self.created_at.date()}): {self.thumbnail_svg.path} ({self.thumbnail_svg.size:,} bytes in {t1 - t0:.2f}s)'
        output += f'\n[{now}] Wrote images for #{self.pk} ({self.created_at.date()}):     {self.svg.path} ({self.svg.size:,} bytes in {t1 - t0:.2f}s)'
        output += f'\n\tWrote PNG thumbnail and file from SVG in {(t2 - t1):.2f}s.'
        return output

    def __str__(self):
        return self.urlhash

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.thumbnail = self.thumbnail.strip()
        super().save(*args, **kwargs)

    DEFER_FIELDS = (
        'mapdata',
        'data',
        'thumbnail',
        'stations',
    )

    class Meta:

        indexes = [
            models.Index(fields=["urlhash"]),
            models.Index(fields=["gallery_visible"]),
            models.Index(fields=["publicly_visible"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["station_count"]),
            models.Index(fields=["name"]),
            models.Index(fields=["likes"]),
            models.Index(fields=["dislikes"]),
            models.Index(fields=["svg"]),
            models.Index(fields=["png"]),
            models.Index(fields=["thumbnail_svg"]),
            models.Index(fields=["thumbnail_png"]),
        ]

        permissions = (
            ('hide_map', "Can set a map's gallery_visible to hidden"),
            ('name_map', "Can set a map's name"),
            ('tag_map', "Can change the tags associated with a map"),
            ('generate_thumbnail', "Can generate thumbnails for a map"), # Now that generating thumbnails is handled differently, should replace
            ('edit_publicly_visible', "Can edit a publicly visible map"),
        )


MAP_TYPE_CHOICES = (
    ('real', 'This is a real map of a real transit system'),
    ('fantasy', 'This is a fantasy map of a real city/transit system'),
    ('imaginary', 'This is an imaginary place'),
)

class IdentifyMap(models.Model):

    """ Crowdsourcing where this map is located,
        and other interesting details
    """

    saved_map = models.ForeignKey(
        'SavedMap',
        on_delete=models.CASCADE,
        help_text="Which map this identification belongs to",
    )
    name = models.CharField(max_length=255)
    map_type = models.CharField(max_length=64, choices=MAP_TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f'Identification #{self.id} for Map #{self.saved_map.id} ({self.saved_map.urlhash})'

class City(models.Model):


    """ The standardized name of a location,
        useful for aggregating queries for the Maps by City view,
        and grouping Montreal with Montréal.
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        return f'City: {self.name}'
