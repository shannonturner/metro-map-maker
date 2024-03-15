from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from map_saver.models import SavedMap

import json
import logging
import time

CHUNK_SIZE = 1000
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
            '-l',
            '--limit',
            type=int,
            dest='limit',
            default=0,
            help='Calculate images and thumbnails for this many maps at once. Not in use if --alltime is set.',
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
        limit = kwargs['limit']
        alltime = kwargs.get('alltime')

        if urlhash:
            needs_images = SavedMap.objects.filter(urlhash=urlhash)
            self.stdout.write(f"Generating images and thumbnails for {urlhash}.")
        elif start:
            needs_images = SavedMap.objects.filter(pk__gte=start)
            self.stdout.write(f"Re-generating images and thumbnails for {limit} maps starting with PK {start}.")
        elif alltime:
            needs_images = SavedMap.objects.all()
            limit = 0
            self.stdout.write(f"Generating images for ALL maps.")
        else:
            needs_images = SavedMap.objects.filter(thumbnail_svg=None)
            limit = limit or 100
            self.stdout.write(f"Generating images and thumbnails for {limit} maps that don't have them.")

        needs_images = needs_images.order_by('pk')
        if limit and not alltime:
            needs_images = needs_images[:limit]

        t0 = time.time()
        for page in Paginator(needs_images, CHUNK_SIZE):
            for mmap in page.object_list:
                t1 = time.time()
                errors = []

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


        t3 = time.time()
        dt = (t3 - t0)
        self.stdout.write(f'Made images and thumbnails in {dt:.2f}s')
        if errors:
            self.stdout.write(f'Failed to generate images and thumbnails for {len(errors)} maps: {errors}')
