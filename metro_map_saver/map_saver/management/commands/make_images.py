from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from map_saver.models import SavedMap

import json
import logging
import time

CHUNK_SIZE = 100
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
        Run on a regular schedule to generate images and thumbnails
            for maps that don't have them yet.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--alltime',
            action='store_true',
            help='Generate images for ALL maps.',
        )
        parser.add_argument(
            '-s',
            '--start',
            type=int,
            dest='start',
            default=0,
            help='(Re-)Calculate images and thumbnails for maps starting with this PK.',
        )
        parser.add_argument(
            '-e',
            '--end',
            type=int,
            dest='end',
            default=0,
            help='Calculate images and thumbnails for maps with a PK lower than this value. Does NOT re-calculate.',
        )
        parser.add_argument(
            '-l',
            '--limit',
            type=int,
            dest='limit',
            default=100,
            help='Only calculate images and thumbnails for this many maps at once. Not in use if --alltime is set.',
        )
        parser.add_argument(
            '-u',
            '--urlhash',
            type=str,
            dest='urlhash',
            default=False,
            help='Calculate images and thumbnails for only one map in particular.',
        )

    def handle(self, *args, **kwargs):
        urlhash = kwargs['urlhash']
        start = kwargs['start']
        end = kwargs['end']
        limit = kwargs['limit']
        alltime = kwargs.get('alltime')
        recalc = False

        if urlhash:
            needs_images = SavedMap.objects.filter(urlhash=urlhash)
            self.stdout.write(f"Generating images and thumbnails for {urlhash}.")
            limit = 1
        elif start:
            needs_images = range(start, start + limit + 1)
            recalc = True
            self.stdout.write(f"Re-generating images and thumbnails for {limit} maps starting with PK {start}.")
        elif end:
            needs_images = range(1, end)
            self.stdout.write(f"Generating images and thumbnails for {limit} maps up to PK {end}.")
        elif alltime:
            needs_images = range(1, SavedMap.objects.count() + 1)
            limit = 0
            recalc = True
            self.stdout.write(f"Generating images for ALL maps.")
        else:
            needs_images = range(1, SavedMap.objects.count() + 1)
            self.stdout.write(f"Generating images and thumbnails for {limit} maps that don't have them.")

        errors = []

        count = 0
        t0 = time.time()
        for page in Paginator(needs_images, CHUNK_SIZE):
            if count >= limit and not alltime:
                break

            if urlhash:
                mmaps = page.object_list
            else:
                # Chunk by PK to save memory, reduce startup time
                mmaps = SavedMap.objects.filter(pk__in=page.object_list)

            self.stdout.write(f'Page {page.number} of {page.paginator.num_pages} (Recalc? {recalc})')
            for mmap in mmaps:
                t1 = time.time()

                try:
                    self.stdout.write(mmap.generate_images())
                except json.decoder.JSONDecodeError as exc:
                    self.stdout.write(f'[ERROR] Failed to generate images and thumbnails for #{mmap.id} ({mmap.urlhash}): JSONDecodeError: {exc}')
                    errors.append(mmap.urlhash)
                except Exception as exc:
                    self.stdout.write(f'[ERROR] Failed to generate images and thumbnails for #{mmap.id} ({mmap.urlhash}): Exception: {exc}')
                    errors.append(mmap.urlhash)
                    raise # DEBUG; TODO -- REMOVE

                t2 = time.time()
                dt = (t2 - t1)
                if dt > 5:
                    logger.warn(f'Generating image for {mmap.urlhash} took a very long time: {dt:.2f}s')

                count += 1
                if count >= limit and not alltime:
                    break

        t3 = time.time()
        dt = (t3 - t0)
        self.stdout.write(f'Made images and thumbnails in {dt:.2f}s')
        if errors:
            self.stdout.write(f'Failed to generate images and thumbnails for {len(errors)} maps: {errors}')
