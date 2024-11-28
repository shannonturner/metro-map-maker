from django.core.management.base import BaseCommand
from map_saver.models import SavedMap
import json

class Command(BaseCommand):
    help = """
        Use to replace specific strings in a SavedMap's mapdata with other strings.
        Use this after making changes to the validation or other cleaning mechanism.

        For instance, in pre-March 2019 versions of MetroMapMaker,
        having a / in the Rail Line name was converted to &#x2f;
        when a dash would actually look much better and have zero security risks.
        (Original example: https://metromapmaker.com/?map=UlXWsVRG)

        Which for the end-user, having a rail name with HTML junk in it
        looks pretty terrible for something so common.
        We can change this going forward,
        but how do we fix all of the old maps that already had this problem?

        Usage:   manage.py replace_mapdata <find> <replace>
        Example: manage.py replace_mapdata "&#x2f;" "-"

        2024 Nov replacements:
            &amp;#x27;  '
            &amp;#x2f;  /
            &amp;amp;   &
            &amp;       &
            --- then ---
            &#x2f;      /
            &#x27;      '

        Use with caution: this could break or otherwise mangle your maps.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'find',
            type=str,
            help='String to search for in the data (v2+)',
        )

        parser.add_argument(
            'replace',
            type=str,
            help='String to replace it with in the data (v2+)',
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
            '--amp',
            action='store_true',
            dest='amp',
            default=False,
            help='Replace all numbers of &amp;amp;'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Dry run to show which maps would be affected.',
        )

    def handle(self, *args, **kwargs):
        limit = kwargs['limit']
        dry_run = kwargs.get('dry_run')
        find = kwargs.get('find')
        replace = kwargs.get('replace')
        amp = kwargs.get('amp')

        amp_replacements = [
            '&' + ('amp;' * x)
            for x in range(60, 0, -1) # A little absurd, but the upper limit of what's allowed
        ]

        saved_maps = SavedMap.objects.raw("SELECT * FROM map_saver_savedmap WHERE LOCATE(%s, data) ORDER BY id", [find])
        self.stdout.write(f"Found {len(saved_maps)} maps that contained the criteria: {find} -- replacement is: {replace}")

        ids_and_hashes = []
        for mmap in saved_maps[:limit]:
            self.stdout.write(f'[MMM-BACKUP] [#{mmap.id}] [{mmap.urlhash}]: {json.dumps(mmap.data)}')

            new_data = json.dumps(mmap.data)
            if amp:
                for amp_replacement in amp_replacements:
                    new_data = new_data.replace(amp_replacement, replace)
            else:
                new_data = new_data.replace(find, replace)

            self.stdout.write(f'\t#{mmap.id}: {new_data}')
            ids_and_hashes.append(f'{mmap.id},{mmap.urlhash}')

            if not dry_run:
                mmap.data = json.loads(new_data)
                mmap.save()

        self.stdout.write(f'Processed the following {len(ids_and_hashes)} maps, worth a spot-check:')
        self.stdout.write('\n'.join(ids_and_hashes))
