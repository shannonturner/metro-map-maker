from django.core.management.base import BaseCommand

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

        Use with caution: this could break or otherwise mangle your maps.
    """

    def add_arguments(self, parser):
        parser.add_argument('find', type=str, help='String to search for in the mapdata')
        parser.add_argument('replace', type=str, help='String to replace it with in the mapdata')

    def handle(self, *args, **kwargs):
        from map_saver.models import SavedMap

        find = kwargs.get('find')
        replace = kwargs.get('replace')

        saved_maps = SavedMap.objects.filter(mapdata__contains=find)
        count = saved_maps.count()
        self.stdout.write(f"Found {count} maps that contained the criteria: {find}")



