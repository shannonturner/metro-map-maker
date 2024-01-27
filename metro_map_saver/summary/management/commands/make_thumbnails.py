from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

import json
import time

class Command(BaseCommand):
    help = """
        Run on a regular schedule to generate thumbails
            for all maps that don't have them yet.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--limit',
            type=int,
            dest='limit',
            default=100,
            help='Calculate thumbnails for this many maps',
        )

    def handle(self, *args, **kwargs):
        needs_thumbnails = SavedMap.objects.filter(thumbnail_svg=None).order_by('pk')
        limit = kwargs['limit']
        self.stdout.write(f"Found {needs_thumbnails.count()} maps that need thumbnails, limiting to {limit} for now.")

        t0 = time.time()
        errors = []

        for mmap in needs_thumbnails[:limit]:
            try:
                self.stdout.write(mmap.generate_svg_thumbnail())
            except json.decoder.JSONDecodeError as exc:
                self.stdout.write(f'[ERROR] Failed to generate thumbail for #{mmap.id} ({mmap.urlhash}): JSONDecodeError: {exc}')
                errors.append(mmap.urlhash)
            except Exception as exc:
                self.stdout.write(f'[ERROR] Failed to generate thumbail for #{mmap.id} ({mmap.urlhash}): JSONDecodeError: {exc}')
                errors.append(mmap.urlhash)

        t1 = time.time()
        self.stdout.write(f'Made {limit} thumbnails in {t1 - t0:.2f}s')
        if errors:
            self.stdout.write(f'Failed to generate thumbnails for {len(errors)} maps: {errors}')
