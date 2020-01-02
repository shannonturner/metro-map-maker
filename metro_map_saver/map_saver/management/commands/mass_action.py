from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = """

        Warning: use with caution.

        Performs the HIDE/SHOW action on a large number of maps matching the criteria.

        Will NEVER act on a map that is publicly visible.

        To use, skim through maps for maps that should not be hidden and tag them first,
            then run this: ./manage.py mass_action 1 hide

        This will hide all gallery visible maps with no tags, no thumbnail, and
            the provided number of stations or fewer.
    """

    def add_arguments(self, parser):
        parser.add_argument('stations', type=int, help='''
            Applies the station_count__lte filter to this QuerySet
        ''')
        parser.add_argument('action', type=str, help='''
            Either "hide" or "show"
        ''')

    def handle(self, *args, **kwargs):
        from map_saver.models import SavedMap

        stations = kwargs['stations']
        action = kwargs['action']

        assert action in ('hide', 'show')

        if action == 'hide':
            gallery_visible = True
        elif action == 'show':
            gallery_visible = False

        maps_to_update = SavedMap.objects.filter(station_count__lte=stations) \
            .filter(tags__exact=None) \
            .filter(thumbnail__exact='') \
            .filter(gallery_visible=gallery_visible)

        count = maps_to_update.count()

        self.stdout.write("{0} maps will be updated".format(maps_to_update.count()))

        for saved_map in maps_to_update.order_by('id'):
            if saved_map.publicly_visible:
                continue
            self.stdout.write("\t#{0}: {1} ({2} stations)".format(
                    saved_map.id,
                    saved_map.urlhash,
                    saved_map.station_count,
                )
            )

        confirmation = str(input("Please enter the number of maps that will be updated to continue: "))
        if int(confirmation) != count:
            self.stdout.write("[EARLY-END] Exiting without editing the maps.")
            return

        for saved_map in maps_to_update.order_by('id'):
            if saved_map.publicly_visible:
                continue
            if action == 'hide':
                saved_map.gallery_visible = False
            elif action == 'show':
                saved_map.gallery_visible = True
            # For logging purposes, the raw ID would let me revert any mistakes the easiest
            self.stdout.write(str(saved_map.id))
            saved_map.save()
        
        self.stdout.write(f"Finished applying {action} to {count} maps.")
