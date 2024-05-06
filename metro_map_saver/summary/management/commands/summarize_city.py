from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from map_saver.models import SavedMap, City
from map_saver.mapdata_optimizer import flatten_nested
from summary.models import MapsByCity

import datetime

class Command(BaseCommand):
    help = """
        Run on a regular schedule to calculate summary stats,
            like the number of maps by city
            to display neat user-facing stats without burdening the database.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--alltime',
            action='store_true',
            help='Calculate maps for all time instead of only last 7 days',
        )

    def handle(self, *args, **kwargs):
        alltime = kwargs.get('alltime')

        # If there are no Cities yet, populate them from common_cities
        if not City.objects.count():
            self.stdout.write(f'[FIRST-RUN] No City objects exist yet, creating from map_saver.common_cities.CITIES')
            from map_saver.common_cities import CITIES
            for city in CITIES:
                City.objects.create(name=city)
            self.stdout.write(f'[FIRST-RUN] Created {City.objects.count()} City objects.')
            # TODO: Consider whether I should keep parity with common_cities.CITIES

        # Find maps that don't have city set, but do have either a name or suggested_city
        maps = SavedMap.objects.filter(city=None).exclude((Q(name='') & Q(suggested_city='')))

        if not alltime:
            since = datetime.date.today() - datetime.timedelta(days=7)
            maps = maps.filter(created_at__date__gte=since)

        if alltime:
            cities_to_check = City.objects.all()
        else:
            city_names = flatten_nested([(m.name, m.suggested_city) for m in maps])
            matching_names = Q()
            for name in city_names:
                name = name.split('(')[0]
                matching_names = matching_names | Q(name__startswith=name)
            if matching_names:
                cities_to_check = City.objects.filter(matching_names)
            else:
                cities_to_check = []

        for city in cities_to_check:
            # TODO: Need also to handle Montreal/Montréal
            matching_city = maps.filter(Q(name__startswith=city.name) | Q(suggested_city__startswith=city.name))
            match_count = matching_city.count()
            self.stdout.write(f'City {city.name} matched {match_count} maps')
            if match_count:
                matching_city.update(city=city)

        for city in City.objects.annotate(num_maps=Count('savedmap')):
            mbc, _ = MapsByCity.objects.get_or_create(city=city)
            mbc.maps = city.num_maps
            mbc.featured = SavedMap.objects.filter(city=city).order_by('-likes', '-created_at').first() or None
            mbc.save()
