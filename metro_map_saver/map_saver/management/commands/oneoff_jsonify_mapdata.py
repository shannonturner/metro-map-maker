from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """

        Before March 2019, MetroMapMaker's mapdata would be saved 
        with Python 2 unicode string artifacts (like u') which would
        need to be converted at the javascript level into valid JSON
        in order to load the map.

        Doing thousands of javascript replacements on every map load
        is silly and slow and completely unnecessary, 
        so storing the maps as valid JSON to begin with is a good idea

        This will convert every map from the old-style formatting
        to the new-style formatting (double quotes instead of single)
        so those replacements don't need to be done every time.

        The old-style is incompatible with the new-style code, 
        and will cause errors (since I need to turn autoescapes off)
        So this must be run after the code is in place and deployed,
        and not before.

        Run this during a maintenance window. 
        This should only ever have to be done once.

    """

    def handle(self, *args, **kwargs):
        from map_saver.models import SavedMap

        for saved_map in SavedMap.objects.all():
            saved_map.mapdata = saved_map.mapdata.replace(" u'", ' "').replace("{u'", '{"').replace("[u'", '["').replace("'", '"')
            saved_map.save()

        count = SavedMap.objects.count()
        self.stdout.write(f"Updated {count} maps to the new-style formatting (double quotes).")