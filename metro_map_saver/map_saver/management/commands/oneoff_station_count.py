from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """

        Before July 2019, the number of stations a map contained
        was a calculated value rather than an attribute.
        Making it an attribute updated on save will improve efficiency,
        especially in reducing the search space in finding similar maps.

        Run this during a maintenance window. 
        This should only ever have to be done once.

    """

    def handle(self, *args, **kwargs):
        from map_saver.models import SavedMap

        maps_to_update = SavedMap.objects.filter(station_count=-1)

        for saved_map in maps_to_update:
            saved_map.save()

        count = maps_to_update.count()
        self.stdout.write(f"Calculated and stored the number of stations for {count} maps.")
