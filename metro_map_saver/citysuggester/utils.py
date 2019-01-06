# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .models import TravelSystem

def load_systems():

    """ Loads all known systems into a dictionary for processing
    """

    systems = {}

    travel_systems = TravelSystem.objects.all()

    for system in travel_systems:
        systems[system.name] = set(system.stations.split('\n'))

    return systems

def suggest_city(map_stations):

    """ Given a set of stations from a map,
        suggest a city it might be located in
        based on known stations in known metro systems
    """

    systems = load_systems()

    possible_cities = {}

    for name, system_stations in systems.items():
        common_stations = system_stations.intersection(map_stations)
        if len(common_stations) > 0:
            possible_cities[name] = len(common_stations) # Or maybe: the set itself, rather than the length
    return sorted(possible_cities.items(), key=lambda kv: kv[1], reverse=True)
