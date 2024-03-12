from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from citysuggester.utils import MINIMUM_STATION_OVERLAP
from map_saver.models import SavedMap

CHUNK_SIZE = 1000

class Command(BaseCommand):
    help = """
        Suggest cities for unnamed maps without suggestions
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-u',
            '--urlhash',
            type=str,
            dest='urlhash',
            default=False,
            help='Suggest cities for only one map in particular.',
        )
        parser.add_argument(
            '-a',
            '--alltime',
            action='store_true',
            help='Suggest cities for all maps; can be useful if new cities have been added.',
        )

    def handle(self, *args, **kwargs):
        urlhash = kwargs['urlhash']
        all_maps = kwargs.get('alltime')
        if urlhash:
            needs_suggestions = SavedMap.objects.filter(urlhash=urlhash)
        elif all_maps:
            needs_suggestions = SavedMap.objects.all()
        else:
            needs_suggestions = SavedMap.objects.filter(suggested_city_overlap=-1)
        
        # Don't bother checking maps that don't have at least this many stations
        needs_suggestions = needs_suggestions.exclude(station_count__lte=MINIMUM_STATION_OVERLAP)

        if all_maps:
            self.stdout.write(f'Checking {needs_suggestions.count()} maps for suggested cities ...')

        for page in Paginator(needs_suggestions.order_by('id'), CHUNK_SIZE):
            for mmap in page.object_list:
                suggested_city = mmap._suggest_city()
                if suggested_city:
                    mmap.suggested_city = suggested_city[0][0].split("(")[0].strip()
                    mmap.suggested_city_overlap = suggested_city[0][1]
                    self.stdout.write(f'{mmap.urlhash} might be {mmap.suggested_city} ({mmap.suggested_city_overlap} stations in common)')
                else:
                    mmap.suggested_city_overlap = 0
                    self.stdout.write(f'{mmap.urlhash} did not match any cities currently in the system.')
                mmap.save()

        self.stdout.write(f'Checked suggestions for {needs_suggestions.count()} maps.')
