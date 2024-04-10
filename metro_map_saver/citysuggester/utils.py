# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv

from .models import TravelSystem

# How many stations in common before a map is considered to be a "match"?
# Only 1 station in common is probably not very useful
MINIMUM_STATION_OVERLAP = 5

def load_systems():

    """ Loads all known systems into a dictionary for processing
    """

    systems = {}

    travel_systems = TravelSystem.objects.all()

    for system in travel_systems:
        systems[system.name] = set(system.stations.split('\n'))

    return systems


def suggest_city(map_stations, station_overlap=MINIMUM_STATION_OVERLAP):

    """ Given a set of stations from a map,
        suggest a city it might be located in
        based on known stations in known metro systems
    """

    possible_cities = {}

    if not station_overlap:
        station_overlap = MINIMUM_STATION_OVERLAP

    systems = load_systems()

    for name, system_stations in systems.items():
        common_stations = system_stations.intersection(map_stations)
        if len(common_stations) > station_overlap:
            possible_cities['{0} ({1})'.format(name, len(system_stations))] = len(common_stations) # Or maybe: the set itself, rather than the length
    return sorted(possible_cities.items(), key=lambda kv: kv[1], reverse=True)


def create_systems_from_csv(csv_file):

    """ Given a properly-formatted CSV file, create TravelSystems for use with citysuggester.

        Example of proper format is:

        "Washington, DC",Philadelphia
        Fort Totten,Erie
        Silver Spring,Allegheny
        Takoma,Cecil B Moore
        ...

        Each system has its own column; the system name is the first row, all stations belonging to that system are in subsequent rows under that column.

        Remember, the point of this is to suggest a meaningful name for someone curating the maps in the admin gallery, so while a city name may be correct for most entries, it won't be enough information for all. For example, if a given city has multiple systems, like San Francisco's BART and MUNI, use "San Francisco BART" or "San Francisco MUNI" as the system name.

        TravelSystem.name must be unique, so this uses update_or_create(), making this safe to run multiple times on a given CSV file, which you might do if updating systems with new stations.

        Intended to run this via a manage.py shell, for example:
            from citysuggester.utils import create_systems_from_csv
            create_systems_from_csv("test-travelsystem-etl.csv")
    """

    systems = {}

    with open(csv_file, 'rb') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            for header, value in row.items():
                if not value.strip():
                    continue # Skip blank lines
                systems.setdefault(header, list()).append(unicode(value, 'utf-8'))

    for system_name, system_stations in systems.items():
        # TravelSystem.save() will process the stations as needed,
        # including replacing any non-ASCII characters and formatting
        # it the same way it does in MetroMapMaker's validator,
        # but it expects a string of stations separated by newlines.
        if system_stations:
            TravelSystem.objects.update_or_create(
                name=system_name,
                defaults={
                    'stations': '\n'.join(system_stations).strip(),
                }
            )
