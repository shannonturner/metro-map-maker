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

        maps_total = SavedMap.objects.filter(gallery_visible=True).count()

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
            'maps_total': maps_total,
            'tags': tags,
            'is_staff': request.user.is_staff,
        }

        return render(request, 'MapGalleryView.html', context)


class MapSimilarView(TemplateView):

    """ Get: Display a gallery of maps that are similar to the specified map.
             This is helpful for quickly browsing maps that are similar to the specified map
                and hopefully hiding ones that are too similar / older versions.

        Since this is so computationally taxing, it's important that this is available
            only to site admins.
    """

    @method_decorator(staff_member_required)
    def get(self, request, **kwargs):

        visible_maps = SavedMap.objects.filter(gallery_visible=True).order_by('id')

        try:
            this_map = SavedMap.objects.get(urlhash=kwargs.get('urlhash'))
        except ObjectDoesNotExist:
            similar_maps = []
        else:
            similar_maps = [this_map]
            possible_matches = []

            sequence_matcher = difflib.SequenceMatcher(a=this_map.mapdata)

            for one_map in visible_maps:
                if one_map.id == this_map.id:
                    # Comparing a map to itself would be a perfect match.
                    #   So don't do it.
                    continue
                else:
                    sequence_matcher.set_seq2(one_map.mapdata)
                    similarity = sequence_matcher.quick_ratio()
                    if similarity >= 0.75:
                        # Similar enough to take a closer look
                        possible_matches.append(one_map)

            similarity_scores = {}
            urlhash_to_map = {} # this is so I can access the map object once it has been sorted by similarity

            # Re-check the maps that were approximated to be pretty close
            for one_map in possible_matches:
                sequence_matcher.set_seq2(one_map.mapdata)
                similarity = sequence_matcher.ratio()
                if similarity >= 0.75:
                    similarity_scores[one_map.urlhash] = similarity
                    urlhash_to_map[one_map.urlhash] = one_map

            # Sort maps by similarity score in descending order
            for map_hash in sorted(similarity_scores, key=similarity_scores.get, reverse=True):
                # How do I sort it in similarity descending?
                # https://docs.python.org/2/library/functions.html#sorted
                # It looks a little something like:
                # a = {
                #     'abcdef01': 0.80,
                #     '12345678': 0.92,
                #     'beeeeeef': 0.76,
                #     '0a0a0a0a': 0.93,
                # }
                # I would want the order to then be:
                #   0a > 12 > ab > be
                # >>> sorted(a, key=a.get, reverse=True)
                # ['0a0a0a0a', '12345678', 'abcdef01', 'beeeeeef']
                similar_maps.append(urlhash_to_map[map_hash])

        context = {
            'headline': 'Maps similar to {0}'.format(kwargs.get('urlhash')),
            'saved_maps': similar_maps,
            'similarity_scores': similarity_scores,
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
