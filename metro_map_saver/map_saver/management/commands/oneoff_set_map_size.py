from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

class Command(BaseCommand):
    help = """
        One-off script to set .map_size
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

    def handle(self, *args, **kwargs):
        limit = kwargs['limit']
        needs_map_size = SavedMap.objects.filter(map_size=-1)
        
        for mmap in needs_map_size[:limit]:

            try:
                map_size = mmap.data.get('global', {}).get('map_size')
            except Exception as exc:
                print(f'[ERROR] Failed to get map_size for {mmap.id} ({mmap.urlhash}): {exc}')
                continue

            if not map_size:
                continue

            mmap.map_size = map_size
            mmap.save()

        self.stdout.write(f'Set map size for {limit} maps.')
