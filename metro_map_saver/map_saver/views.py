# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

import difflib
import hashlib
import json
import logging
import pprint

from taggit.models import Tag

from .models import SavedMap
from .validator import is_hex, sanitize_string, validate_metro_map, hex64

# Create your views here.
logging.basicConfig(
    filename="mapvalidationfailed.log",
    filemode="a",
    level=logging.ERROR,
    format='%(asctime)s %(message)s',
)

class MapGalleryView(TemplateView):

    """ Get: Display a gallery of maps that have been saved in the system.
             This is helpful for quickly browsing maps that have been created.
    """

    def get(self, request, **kwargs):

        MAPS_PER_PAGE = 25

        tags = Tag.objects.all().order_by('id')

        if kwargs.get('tag') == 'notags':
            visible_maps = SavedMap.objects.filter(gallery_visible=True).filter(tags__exact=None).order_by('id')
        elif kwargs.get('tag') in [t.name for t in tags]:
            visible_maps = SavedMap.objects.filter(gallery_visible=True).filter(tags__name=kwargs.get('tag')).order_by('id')
        else:
            visible_maps = SavedMap.objects.filter(gallery_visible=True).order_by('id')

        paginator = Paginator(visible_maps, MAPS_PER_PAGE)

        page = kwargs.get('page')
        try:
            saved_maps = paginator.page(page)
        except PageNotAnInteger:
            saved_maps = paginator.page(1)
        except EmptyPage:
            saved_maps = paginator.page(paginator.num_pages)

        context = {
            'saved_maps': saved_maps,
            'maps_total': visible_maps.count(),
            'tags': tags,
            'is_staff': request.user.is_staff,
        }

        return render(request, 'MapGalleryView.html', context)

def load_map_data(saved_map):

    """ Returns a JSON object of a saved_map's mapdata
    """

    return json.loads(
                str(
                    json.loads(
                        json.dumps(
                            saved_map.mapdata.replace("u'", "'").replace("'", '"').strip('"').strip("'")
                        )
                    )
                )
            )

def get_stations(mapdata):

    """ Returns a set of station names from a given mapdata
    """

    stations = set()

    for x in mapdata:
        for y in mapdata[x]:
            stations.add(mapdata[x][y].get('station', {}).get('name'))

    return stations

class MapSimilarView(TemplateView):

    """ Get: Display a gallery of maps that are similar to the specified map.
             This is helpful for quickly browsing maps that are similar to the specified map
                and hopefully hiding ones that are too similar / older versions.

        Since this is so computationally taxing, it's important that this is available
            only to site admins.
            ^ Since moving to only checking by station names, performance is improved
                but I'm going to keep the staff_member_required designation
    """

    @method_decorator(staff_member_required)
    def get(self, request, **kwargs):

        visible_maps = SavedMap.objects.filter(gallery_visible=True).order_by('id')
        tags = Tag.objects.all().order_by('id')

        try:
            this_map = SavedMap.objects.get(urlhash=kwargs.get('urlhash'))
        except ObjectDoesNotExist:
            similar_maps = []
            similarity_scores = {}
        else:
            similar_maps = [this_map]

            this_mapdata = load_map_data(this_map)
            this_map_stations = get_stations(this_mapdata)

            similar_maps = []
            similarity_scores = {}
            urlhash_to_map = {} # this is so I can access the map object once it has been sorted by similarity

            for one_map in visible_maps:
                if one_map.id == this_map.id:
                    # Comparing a map to itself would be a perfect match.
                    #   So don't do it.
                    continue
                else:
                    try:
                        one_mapdata = load_map_data(one_map)
                        one_map_stations = get_stations(one_mapdata)
                    except Exception:
                        # If a map failed to load, it's not going to be similar
                        continue

                    if len(this_map_stations) == 0 or len(one_map_stations) == 0:
                        continue

                    overlap = len(this_map_stations.intersection(one_map_stations)) / float(len(this_map_stations))
                    difference = 1.0 - (len(one_map_stations - this_map_stations) / float(len(this_map_stations)))

                    similarity = (overlap * difference)

                    if similarity >= 0.8:
                        # If there's an overlap of 80% of stations by name, they are probably pretty similar
                        similar_maps.append(one_map)
                        similarity_scores[one_map.urlhash] = similarity
                        urlhash_to_map[one_map.urlhash] = one_map

            similar_maps.sort(key=similarity_scores.get, reverse=True)

            # It's easier to compare the maps if I can also see the base map on the similarity page
            similar_maps.insert(0, this_map)

        context = {
            'headline': 'Maps similar to {0}'.format(kwargs.get('urlhash')),
            'saved_maps': similar_maps,
            'similarity_scores': similarity_scores,
            'tags': tags,
            'is_staff': request.user.is_staff,
        }

        return render(request, 'MapGalleryView.html', context)


class MapAdminActionView(TemplateView):

    @method_decorator(staff_member_required)
    def post(self, request, **kwargs):

        """ Perform an administrator action on a map
        """

        context = {}

        if request.POST.get('action') in ('hide', 'addtag', 'removetag',) and request.POST.get('map'):
            try:
                this_map = SavedMap.objects.get(id=request.POST.get('map'))
            except ObjectDoesNotExist:
                context['status'] = '[ERROR] Map does not exist.'
            else:
                if request.POST.get('action') == 'hide':
                    this_map.gallery_visible = False
                    this_map.save()
                elif request.POST.get('action') in ('addtag', 'removetag'):
                    tag = request.POST.get('tag')
                    if tag:
                        if request.POST.get('action') == 'addtag':
                            this_map.tags.add(tag)
                        elif request.POST.get('action') == 'removetag':
                            this_map.tags.remove(tag)
                        this_map.save()
                context['status'] = 'Success'
            return render(request, 'MapAdminActionView.html', context)


class MapDiffView(TemplateView):

    def get(self, request, **kwargs):

        """ Compare two similar maps and return a diff
        """

        context = {}
        maps = []

        pretty_printer = pprint.PrettyPrinter(indent=1)

        try:
            maps.append(SavedMap.objects.get(urlhash=kwargs.get('urlhash_first')))
            maps.append(SavedMap.objects.get(urlhash=kwargs.get('urlhash_second')))
        except ObjectDoesNotExist:
            context['error'] = '[ERROR] One or both of the maps does not exist (either {0} or {1})'.format(kwargs.get('urlhash_first'), kwargs.get('urlhash_second'))
        except MultipleObjectsReturned:
            context['error'] = '[ERROR] Multiple objects returned during an objects.get() call. This should never happen.'
        else:

            context['maps'] = maps[:]

            for index, metro_map in enumerate(maps):
                # It's excessively silly that I need to json.loads() twice here
                #       but this is the ONLY thing that I could actually get to work after
                #       many, many hours of trying.
                # Maybe this is easier in Python 3?
                maps[index] = pretty_printer.pformat(
                    json.loads(
                        str(
                            json.loads(
                                json.dumps(
                                    metro_map.mapdata.replace("u'", "'").replace("'", '"').strip('"').strip("'")
                                )
                            )
                        )
                    )
                )

            diff = difflib.ndiff(maps[0].splitlines(1), maps[1].splitlines(1))

            context['diff'] = []

            for line in diff:
                if line[0] in ('+', '-'):
                    context['diff'].append(line.strip().replace("u'", "'").replace('  ', ' ').replace('  ', ' '))

        return render(request, 'MapDiffView.html', context)


class MapDataView(TemplateView):

    """ Get: Given a hash URL, load a saved map
        Post: Save your map and generate a hash URL to facilitate sharing
    """

    def get(self, request, **kwargs):
        urlhash = kwargs.get('urlhash')

        context = {}

        try:
            saved_map = SavedMap.objects.get(urlhash=urlhash)
        except ObjectDoesNotExist:
            context['error'] = '[ERROR] The requested map does not exist ({0})'.format(urlhash)
        except MultipleObjectsReturned:
            context['error'] = '[ERROR] Multiple objects returned ({0}). This should never happen.'.format(urlhash)
        else:
            context['saved_map'] = saved_map.mapdata

        return render(request, 'MapDataView.html', context)

    def post(self, request, **kwargs):
        mapdata = request.POST.get('metroMap')

        context = {}

        try:
            mapdata = validate_metro_map(mapdata)
        except AssertionError, e:
            context['error'] = '[ERROR] Map failed validation! ({0}) -- map was {1}'.format(e, mapdata)
            logging.error('[ERROR] [FAILEDVALIDATION] ({0}); mapdata: {1}'.format(e, mapdata))
        else:
            urlhash = hex64(hashlib.sha256(str(mapdata)).hexdigest()[:12])
            try:
                # Doesn't override the saved map if it already exists.
                saved_map = SavedMap.objects.get(urlhash=urlhash)
            except ObjectDoesNotExist:
                saved_map = SavedMap(**{
                    'urlhash': urlhash,
                    'mapdata': mapdata,
                    })
                saved_map.save()

            context['saved_map'] = saved_map.urlhash

        return render(request, 'MapDataView.html', context)
