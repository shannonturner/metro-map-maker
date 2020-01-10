from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

class Command(BaseCommand):
    help = """
        Runs .save() on every map that matches the non-tag criteria for ._publicly_visible
        in order to set .publicly_visible (it defaults to False, so this is safe)
    """

    def handle(self, *args, **kwargs):
        maps_to_update = SavedMap.objects \
            .filter(gallery_visible=True) \
            .exclude(publicly_visible=True) \
            .exclude(thumbnail__exact='') \
            .exclude(name__exact='') \
            .exclude(tags__slug='reviewed')

        count = maps_to_update.count()
        self.stdout.write("{0} maps will be .save()'d to set .publicly_visible".format(maps_to_update.count()))

        for saved_map in maps_to_update.order_by('id'):
            if saved_map.publicly_visible:
                continue

            # For logging purposes, write the raw ID
            self.stdout.write(str(saved_map.id))
            saved_map.save()

        self.stdout.write(f"Finished .save() on {count} maps.")
