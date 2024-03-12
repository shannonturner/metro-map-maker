from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

import json

class Command(BaseCommand):
    help = """
        Run to generate v2-style mapdata
            for maps that don't have it yet.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--chunksize',
            type=int,
            dest='chunksize',
            default=1000,
            help='Generate mapdata for this many maps at a time (but they will all be processed)',
        )
        parser.add_argument(
            '-u',
            '--urlhash',
            type=str,
            dest='urlhash',
            default=False,
            help='Generate mapdata for only one map in particular.',
        )

    def handle(self, *args, **kwargs):
        from map_saver.models import SavedMap

        chunksize = kwargs.get('chunksize')
        urlhash = kwargs.get('urlhash')

        if urlhash:
            maps_to_update = SavedMap.objects.filter(urlhash=urlhash)
        else:
            maps_to_update = SavedMap.objects.filter(data={})
        count = maps_to_update.count()

        for page in Paginator(maps_to_update.order_by('id'), chunksize):

            if chunksize >= 1000:
                self.stdout.write(f"Generating v2 mapdata for {page.start_index()} - {page.end_index()} (of {count})")

            for saved_map in page.object_list:
                try:
                    saved_map.convert_mapdata_v1_to_v2()
                except json.decoder.JSONDecodeError:
                    print(f'[WARN] JSONDecodeError for {saved_map.urlhash}') # Will need to manually fix these
                    continue
                except Exception as exc:
                    print(f'[WARN] Exception {exc} for {saved_map.urlhash}')
                    continue

                if chunksize < 1000:
                    self.stdout.write(f"Generated v2 mapdata for {saved_map.urlhash}")
