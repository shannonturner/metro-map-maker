from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

import json
import time

class Command(BaseCommand):
    help = """
        Run to generate v2-style mapdata
            for maps that don't have it yet.
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
            help='Generate mapdata for only one map in particular.',
        )

        parser.add_argument(
            '--ongoing',
            action='store_true',
            dest='ongoing',
            default=False,
            help='Run ongoing to ensure v1-created maps get converted to v2 in real time',
        )

    def handle(self, *args, **kwargs):

        urlhash = kwargs.get('urlhash')
        start = kwargs['start']
        end = kwargs['end']
        limit = kwargs['limit']
        ongoing = kwargs.get('ongoing')

        if urlhash:
            limit = total = 1
            maps_to_update = SavedMap.objects.filter(urlhash=urlhash).order_by('id')[:limit]
        elif start or end:
            start = start or 1
            end = end or (start + limit + 1)
            maps_to_update = SavedMap.objects.filter(pk__in=range(start, end))
            if ongoing:
                maps_to_update = maps_to_update.filter(data={})
            maps_to_update = maps_to_update.order_by('id')[:limit]
        else:
            maps_to_update = SavedMap.objects.filter(data={}).order_by('id')[:limit]

        total = maps_to_update.count()
        self.stdout.write(f'Generating v2 mapdata for {total} maps')

        t0 = time.time()

        for saved_map in maps_to_update:
            try:
                saved_map.convert_mapdata_v1_to_v2()
            except json.decoder.JSONDecodeError:
                if not saved_map.mapdata:
                    # These are test maps that started in v2 made in dev/staging
                    #   and don't need to be converted, but this is being run
                    #   after these maps were made
                    self.stdout.write(f'Skipping dev/staging map {saved_map.urlhash}')
                    continue
                self.stdout.write(f'[WARN] JSONDecodeError for {saved_map.urlhash})') # Will need to manually fix these
                continue
            except Exception as exc:
                self.stdout.write(f'[WARN] Exception {exc} for {saved_map.urlhash}')
                continue
            else:
                self.stdout.write(f'Generated v2 data for #{saved_map.id}: {saved_map.urlhash} ({saved_map.created_at.date()})')

        t1 = time.time()
        self.stdout.write(f'Finished in {(t1 - t0):.2f}s')
