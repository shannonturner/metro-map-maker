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
import pprint
from .models import SavedMap
from .validator import is_hex, sanitize_string, validate_metro_map, hex64

# Create your views here.

class MapGalleryView(TemplateView):

    """ Get: Display a gallery of maps that have been saved in the system.
             This is helpful for quickly browsing maps that have been created.
    """

    def get(self, request, **kwargs):

        MAPS_PER_PAGE = 10

        maps_total = SavedMap.objects.filter(gallery_visible=True).count()

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
            'is_staff': request.user.is_staff,
        }

        return render(request, 'MapGalleryView.html', context)


class MapAdminActionView(TemplateView):

    @method_decorator(staff_member_required)
    def post(self, request, **kwargs):

        """ Perform an administrator action on a map
        """

        context = {}

        if request.POST.get('action') in ('hide', ) and request.POST.get('map'):
            try:
                this_map = SavedMap.objects.get(id=request.POST.get('map'))
            except ObjectDoesNotExist:
                context['status'] = '[ERROR] Map does not exist.'
            else:
                if request.POST.get('action') == 'hide':
                    this_map.gallery_visible = False
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
