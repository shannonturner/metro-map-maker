from django.core.management.base import BaseCommand

from citysuggester.utils import MINIMUM_STATION_OVERLAP
from map_saver.models import SavedMap

import time

class Command(BaseCommand):
    help = """
        Suggest cities for unnamed maps without suggestions
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--start',
            type=int,
            dest='start',
            default=0,
            help='(Re-)calculate data for maps starting with this PK.',
        )
        parser.add_argument(
            '-e',
            '--end',
            type=int,
            dest='end',
            default=0,
            help='Process maps with a PK lower than this value. Does NOT process maps that already have v2 data.',
        )
        parser.add_argument(
            '-l',
            '--limit',
            type=int,
            dest='limit',
            default=1000,
            help='Only process this many maps at once.',
        )
        parser.add_argument(
            '-u',
            '--urlhash',
            type=str,
            dest='urlhash',
            default=False,
            help='Suggest cities for only one map in particular.',
        )

    def handle(self, *args, **kwargs):
        urlhash = kwargs['urlhash']
        start = kwargs['start']
        end = kwargs['end']
        limit = kwargs['limit']

        if urlhash:
            limit = 1
            needs_suggestions = SavedMap.objects.filter(urlhash=urlhash)
        elif start or end:
            start = start or 1
            end = end or (start + limit + 1)
            needs_suggestions = SavedMap.objects.filter(pk__in=range(start, end))
        else:
            needs_suggestions = SavedMap.objects.filter(suggested_city_overlap=-1)

        # Don't bother checking maps that don't have stations (-1, implied by lte MINIMUM),
        #   or those that don't have at least this many stations
        needs_suggestions = needs_suggestions.exclude(station_count__lte=MINIMUM_STATION_OVERLAP)
        needs_suggestions = needs_suggestions.order_by('id')[:limit]

        self.stdout.write(f'Checking {needs_suggestions.count()} maps for suggested cities ...')
        t0 = time.time()

        for mmap in needs_suggestions:
            suggested_city = mmap._suggest_city()
            if suggested_city:
                mmap.suggested_city = suggested_city[0][0].split("(")[0].strip()
                mmap.suggested_city_overlap = suggested_city[0][1]
                self.stdout.write(f'#{mmap.id}: {mmap.urlhash} ({mmap.created_at.date()}) might be {mmap.suggested_city} ({mmap.suggested_city_overlap} stations in common)')
            else:
                mmap.suggested_city_overlap = 0
                self.stdout.write(f'#{mmap.id}: {mmap.urlhash} ({mmap.created_at.date()}) did not match any cities currently in the system.')
            mmap.save()

        t1 = time.time()
        self.stdout.write(f'Finished in {(t1 - t0):.2f}s')
