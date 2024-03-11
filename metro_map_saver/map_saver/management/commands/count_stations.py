from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

class Command(BaseCommand):
    help = """
        Run on a regular schedule to:
            count stations into .station_count
            and populate .stations
    """

    def handle(self, *args, **kwargs):
        needs_stations = SavedMap.objects.filter(station_count=-1)
        
        for mmap in needs_stations:
            mmap.stations = mmap._get_stations()
            mmap.station_count = mmap._station_count()
            mmap.save()
