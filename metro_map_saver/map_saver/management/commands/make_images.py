from django.core.management.base import BaseCommand
from django.db.models import Q
from map_saver.models import SavedMap

import json
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
        Run on a regular schedule to generate images and thumbnails.

            This really has multiple modes:
                * ongoing (no args), less memory-efficient but with fewer database hits,
                    meant to generate maps for the first time automatically on a schedule
                * urlhash, meant to (re-)generate a single map
                * start/end, like alltime but meant to handle picking up from a starting point
    """

    def add_arguments(self, parser):
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
            default=500,
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

        if urlhash:
            limit = total = 1
            needs_images = SavedMap.objects.filter(urlhash=urlhash)
            self.stdout.write(f"Generating images and thumbnails for {urlhash}.")
            limit = 1
        elif start or end:
            start = start or 1
            end = end or (start + limit + 1)
            needs_images = SavedMap.objects.filter(pk__in=range(start, end))
            self.stdout.write(f"(Re-)Generating images and thumbnails for {limit} maps starting with PK {start}.")
        else:
            # .filter(thumbnail_svg__in=[None, '']) worked great on staging until it didn't;
            #   then staging would only match on thumbnail_svg=None;
            #   using Q() objects works equally well on both
            needs_images = SavedMap.objects.filter(Q(thumbnail_svg=None) | Q(thumbnail_svg=''))
            self.stdout.write(f"Generating images and thumbnails for up to {limit} maps that don't have them.")

        needs_images = needs_images.order_by('id')[:limit]

        errors = []
        t0 = time.time()
        for mmap in needs_images:
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

        t3 = time.time()
        dt = (t3 - t0)
        self.stdout.write(f'Made images and thumbnails in {dt:.2f}s')
        if errors:
            self.stdout.write(f'Failed to generate images and thumbnails for {len(errors)} maps: {errors}')
