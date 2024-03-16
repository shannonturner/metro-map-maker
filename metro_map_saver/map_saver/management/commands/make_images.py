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
        Run on a regular schedule to generate images and thumbnails.

            This really has multiple modes:
                * alltime, a memory-efficient method meant to generate images the first time,
                    or re-generate them ALL if I ever made any major rendering changes
                * ongoing (no args), less memory-efficient but with fewer database hits,
                    meant to generate maps for the first time automatically on a schedule
                * urlhash, meant to (re-)generate a single map
                * start, like alltime but meant to handle picking up from a starting point
                    (if alltime only partially ran, for example, it's useful to not start over)

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
            default=CHUNK_SIZE * 5,
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

        if urlhash:
            needs_images = SavedMap.objects.filter(urlhash=urlhash).order_by('id')[:limit]
            self.stdout.write(f"Generating images and thumbnails for {urlhash}.")
            limit = 1
        elif alltime:
            # In practice, I probably won't be able to use this
            #   on staging/prod unless I want to tracemalloc the memory leak
            needs_images = range(1, SavedMap.objects.count() + 1)
            limit = 0
            self.stdout.write(f"Generating images for ALL maps.")
        elif start or end:
            start = start or 1
            end = end or (start + limit + 1)
            needs_images = range(start, end)
            self.stdout.write(f"Re-generating images and thumbnails for {limit} maps starting with PK {start}.")
        else:
            needs_images = SavedMap.objects.filter(thumbnail_svg__in=[None, '']).order_by('id')[:limit]
            self.stdout.write(f"Generating images and thumbnails for {limit} maps that don't have them.")

        errors = []

        count = 0
        t0 = time.time()
        for page in Paginator(needs_images, CHUNK_SIZE):
            if count >= limit and not alltime:
                break

            if isinstance(needs_images, range):
                # Chunk by PK to save memory, reduce startup time
                mmaps = SavedMap.objects.filter(pk__in=page.object_list)
            else:
                mmaps = page.object_list

            self.stdout.write(f'Page {page.number} of {page.paginator.num_pages}')
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

                t2 = time.time()
                dt = (t2 - t1)
                if dt > 5:
                    self.stdout.write(f'Generating image for {mmap.urlhash} took a very long time: {dt:.2f}s')
                    logger.warn(f'Generating image for {mmap.urlhash} took a very long time: {dt:.2f}s')

                count += 1
                if count >= limit and not alltime:
                    break

        t3 = time.time()
        dt = (t3 - t0)
        self.stdout.write(f'Made images and thumbnails in {dt:.2f}s')
        if errors:
            self.stdout.write(f'Failed to generate images and thumbnails for {len(errors)} maps: {errors}')
