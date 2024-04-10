from django.core.management.base import BaseCommand
from map_saver.models import SavedMap

import datetime
import math
import pytz


class Command(BaseCommand):
    help = """
        Backdates old maps (from prior to addition of .created_at, sigh)
        based on best-available data I have.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='TK.',
        )

    def handle(self, *args, **kwargs):

        dry_run = kwargs['dry_run']

        UTC = pytz.timezone('UTC')

        key_dates = {
            "2018-04-11": 218,
            "2018-06-20": 70,
            "2018-07-14": 24,
            "2018-07-25": 11,
            "2018-07-31": 6,
            "2018-08-11": 11,
            "2018-08-30": 19,
            "2018-09-12": 13,
        }

        for old_date, days_elapsed in key_dates.items():

            old_date = datetime.datetime.strptime(old_date, '%Y-%m-%d')
            old_date = old_date.replace(tzinfo=UTC)

            days = days_elapsed - 1
            maps_this_date = list(SavedMap.objects.filter(created_at=old_date).order_by('id'))
            map_count = len(maps_this_date)
            maps_to_backdate = []

            if map_count < days_elapsed:
                raise ValueError('This command has already been run! Exiting now.')

            # Make sure at least this many maps get created each day;
            # though we will need to add the remainders on still
            maps_per_day = [math.floor(map_count / days_elapsed)] * days_elapsed
            remainder = map_count - sum(maps_per_day)
            index = 0
            while remainder > 0:
                maps_per_day[index] += 1
                remainder -= 1
                index += 1

            self.stdout.write(f"Found {map_count} maps for {old_date}")

            for mmap in maps_this_date:
                maps_to_backdate.append(mmap)
                if len(maps_to_backdate) >= maps_per_day[days - 1]:
                    new_date = old_date - datetime.timedelta(days=days)
                    self.stdout.write(f"{'[DRY-RUN] ' if dry_run else ''} Set date from {old_date.date()} to {new_date.date()} for {[m.pk for m in maps_to_backdate]}")
                    if not dry_run:
                        SavedMap.objects.filter(pk__in=[m.pk for m in maps_to_backdate]).update(
                            created_at=new_date,
                        )
                    days = days - 1
                    maps_to_backdate = []
            else:
                if maps_to_backdate:
                    new_date = old_date - datetime.timedelta(days=days_elapsed)
                    self.stdout.write(f"{'[DRY-RUN] ' if dry_run else ''} Set date from {old_date.date()} to {new_date.date()} for {[m.pk for m in maps_to_backdate]}")
                    if not dry_run:
                        SavedMap.objects.filter(pk__in=[m.pk for m in maps_to_backdate]).update(
                            created_at=new_date,
                        )
