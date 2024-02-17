from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import TruncDate

from map_saver.models import SavedMap
from summary.models import MapsByDay

import datetime

class Command(BaseCommand):
    help = """
        Run on a regular schedule to calculate summary stats,
            like the number of maps created by day
            to display neat user-facing stats without burdening the database.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--alltime',
            action='store_true',
            help='Calculate maps by day for all time instead of only last 7 days',
        )

    def handle(self, *args, **kwargs):

        # Maps by Day
        if kwargs.get('alltime'):
            since = datetime.date(2017, 9, 5)
        else:
            since = datetime.date.today() - datetime.timedelta(days=7)
        self.stdout.write(f"Calculating counts of maps by day since: {since}")

        maps_by_day = SavedMap.objects.filter(created_at__date__gte=since)
        maps_by_day = maps_by_day.values(day=TruncDate('created_at')).annotate(Count('day')).order_by('day')

        self.stdout.write(f"Found {maps_by_day.count()} days to check")

        for mbd in maps_by_day:
            self.stdout.write(f"{mbd['day']}:\t{mbd['day__count']}")
            mbd_obj = MapsByDay.objects.filter(day=mbd['day'])
            if mbd_obj:
                assert mbd_obj.count() == 1
                mbd_obj = mbd_obj.last()
                mbd_obj.maps = mbd['day__count']
                mbd_obj.save()
            else:
                mbd_obj = MapsByDay.objects.create(
                    day=mbd['day'],
                    maps=mbd['day__count'],
                )
