from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

import json
import time

class Command(BaseCommand):
    help = """
        Run on a regular schedule to generate images and thumbnails
            for maps that don't have them yet.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--pk',
            type=int,
            dest='pk',
            default=0,
            help='(Re-)Calculate images and thumbnails for maps starting with this PK.',
        )
        parser.add_argument(
            '-l',
            '--limit',
            type=int,
            dest='limit',
            default=100,
            help='Calculate images and thumbnails for this many maps',
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
        pk = kwargs['pk']
        if urlhash:
            # This will let me re-generate
            needs_thumbnails = SavedMap.objects.filter(urlhash=urlhash)
            limit = 1
            self.stdout.write(f"Generating images and thumbnails for {urlhash}.")
        elif pk:
            needs_thumbnails = SavedMap.objects.filter(pk__gte=pk).order_by('pk')
            limit = kwargs['limit']
            self.stdout.write(f"Re-generating images and thumbnails for {limit} maps starting with PK {pk}.")
        else:
            needs_thumbnails = SavedMap.objects.filter(thumbnail_svg=None).order_by('pk')
            limit = kwargs['limit']
            self.stdout.write(f"Found {needs_thumbnails.count()} maps that need images and thumbnails, limiting to {limit} for now.")

        t0 = time.time()
        errors = []

        for mmap in needs_thumbnails[:limit]:
            try:
                self.stdout.write(mmap.generate_images())
            except json.decoder.JSONDecodeError as exc:
                self.stdout.write(f'[ERROR] Failed to generate images and thumbnails for #{mmap.id} ({mmap.urlhash}): JSONDecodeError: {exc}')
                errors.append(mmap.urlhash)
            except Exception as exc:
                self.stdout.write(f'[ERROR] Failed to generate images and thumbnails for #{mmap.id} ({mmap.urlhash}): Exception: {exc}')
                errors.append(mmap.urlhash)
                raise # DEBUG; TODO -- REMOVE

        t1 = time.time()
        self.stdout.write(f'Made {limit} images and thumbnails in {t1 - t0:.2f}s')
        if errors:
            self.stdout.write(f'Failed to generate images and thumbnails for {len(errors)} maps: {errors}')
