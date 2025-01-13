from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

class Command(BaseCommand):
    help = """
        One-off script to fix the ~300 map names that have ampersands
            corrupted to &amp;amp;
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--limit',
            type=int,
            dest='limit',
            default=1000,
            help='Only process this many maps at once.',
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Dry run to show which maps and replacements would occur, but do not actually change any maps.',
        )

    def handle(self, *args, **kwargs):
        limit = kwargs['limit']
        dry_run = kwargs.get('dry_run')
        needs_editing = SavedMap.objects.filter(name__contains='&amp;')
        count = needs_editing.count()

        replacements = [
            '&' + ('amp;' * 5),
            '&' + ('amp;' * 4),
            '&' + ('amp;' * 3),
            '&' + ('amp;' * 2),
            '&' + ('amp;'),
        ]

        for mmap in needs_editing[:limit]:

            new_name = mmap.name
            for replacement in replacements:
                new_name = new_name.replace(replacement, '&')

            if dry_run:
                print(f'Would rename {mmap.id} (from {mmap.name} to {new_name})')
            else:
                mmap.name = new_name
                mmap.save()

        self.stdout.write(f'{"Would replace" if dry_run else "Replaced"} &amp; to ampersands in the name for {min(count, limit)} maps.')
