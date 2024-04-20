
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, PermissionDenied
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.gzip import gzip_page
from django.views.decorators.cache import cache_page, never_cache, cache_control
from django.conf import settings
from django.views.generic.dates import (
    DayArchiveView,
)

import base64
import datetime
import difflib
import json
import logging
import os
import pprint
import pytz
import random
import requests
import urllib.parse

from taggit.models import Tag

from moderate.models import ActivityLog
from citysuggester.models import TravelSystem
from .forms import (
    CreateMapForm,
    IdentifyForm,
    RateForm,
)
from .models import SavedMap, IdentifyMap
from .validator import (
    is_hex,
    sanitize_string,
    validate_metro_map,
    hex64,
    ALLOWED_TAGS,
    ALLOWED_MAP_SIZES,
)

logger = logging.getLogger(__name__)

class HomeView(TemplateView):

    template_name = 'index.html'

    @method_decorator(gzip_page)
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, **kwargs):
        urlhash = kwargs.get('urlhash', request.GET.get('map'))
        if not urlhash:
            # Only show favorite thumbnails if we're NOT loading a specific map,
            #   otherwise that wastes a bit of bandwidth and pagespeed
            #   which is especially important since this only shows on mobile
            thumbnails = SavedMap.objects \
                .filter(gallery_visible=True) \
                .exclude(thumbnail__exact='') \
                .exclude(name__exact='') \
                .exclude(tags__slug='reviewed') \
                .filter(tags__slug='favorite') \
                .order_by('?')

            context = {
                'favorites': thumbnails[:3]
            }
        else:
            try:
                saved_map = SavedMap.objects.get(urlhash=urlhash)
            except MultipleObjectsReturned:
                saved_map = SavedMap.objects.filter(urlhash=urlhash).first()
            except ObjectDoesNotExist:
                context = {
                    'today': timezone.now().date(),
                    'error': 'Map was not found.',
                }
                return render(request, self.template_name, context)
            except Exception as exc:
                context = {
                    'today': timezone.now().date(),
                    'error': f'This map could not be loaded: {exc}'
                }
                return render(request, self.template_name, context)

            context = {
                'saved_map': saved_map,
            }
            if saved_map.name:
                if saved_map.name.endswith(' (real)'):
                    context["saved_map_name"] = saved_map.name.rsplit(" (real)")[0]
                elif saved_map.name.endswith(' (speculative)'):
                    context["saved_map_name"] = saved_map.name.rsplit(" (speculative)")[0]
                elif saved_map.name.endswith(' (unknown)'):
                    context["saved_map_name"] = saved_map.name.rsplit(" (unknown)")[0]
                else:
                    context["saved_map_name"] = saved_map.name
            try:
                context['canvas_size'] = saved_map['global']['map_size'] * 20
            except Exception:
                context['canvas_size'] = 1600

        context['today'] = timezone.now().date()
        context['ALLOWED_MAP_SIZES'] = ALLOWED_MAP_SIZES

        return render(request, self.template_name, context)


class PublicGalleryView(TemplateView):

    template_name = 'PublicGallery.html'

    @method_decorator(gzip_page)
    def get(self, request, **kwargs):
        return super().get(request, **kwargs)

    def get_context_data(self, *args, **kwargs):

        context = super().get_context_data(*args, **kwargs)

        tags = [
            'favorite',
            'real',
            # As long as we're fetching these ajaxy, no sense in loading them here too
            # 'speculative',
            # 'unknown',
        ]

        thumbnails = SavedMap.objects.defer('mapdata', 'data', 'stations').filter(publicly_visible=True)

        for tag in tags:
            context[tag] = thumbnails.filter(tags__slug=tag).order_by('name')
        context['favorite'] = context['favorite'].order_by('?')[:8]

        from summary.models import MapsByDay
        mbd = MapsByDay.objects.all()
        context['map_count'] = sum(m.maps for m in mbd)

        return context

class ThumbnailGalleryView(TemplateView):

    @method_decorator(gzip_page)
    def get(self, request, **kwargs):

        thumbnails = SavedMap.objects \
            .filter(publicly_visible=True) \
            .exclude(name__exact='') \
            .exclude(tags__slug='reviewed')

        if kwargs.get('tag'):
            thumbnails = thumbnails.filter(tags__slug=kwargs.get('tag'))

        if kwargs.get('tag') == 'favorite':
            thumbnails = thumbnails.order_by('?')[:8]
        else:
            thumbnails = thumbnails.order_by('name')

        context = {
            'thumbnails': thumbnails.defer('mapdata', 'data', 'stations'),
        }
        return render(request, 'thumbnails.html', context)

class MapGalleryView(TemplateView):

    """ Get: Display a gallery of maps that have been saved in the system.
             This is helpful for quickly browsing maps that have been created.
    """

    @method_decorator(gzip_page)
    @method_decorator(login_required)
    def get(self, request, **kwargs):

        MAPS_PER_PAGE = 25
        NON_FILTERABLE = (
            'page',
            'per_page',
            'order_by',
        )

        tags = Tag.objects.all().order_by('id')

        if request.GET.get('map') or kwargs.get('direct'):
            # Accessible either by
            #           /admin/direct/https://metromapmaker.com/?map=8RkQTRav
            #   or by   /admin/direct/8RkQTRav
            direct = request.GET.get('map', kwargs.get('direct', '')[-8:])
            visible_maps = SavedMap.objects.filter(urlhash=direct)
            filters = None
        else:
            # Most common usage is to see gallery visible maps,
            #   but it should be possible to view non-visible maps too
            gallery_visible = request.GET.get('gallery_visible', True)
            if gallery_visible in ('0', 'False', 'false'):
                gallery_visible = False
            visible_maps = SavedMap.objects.filter(gallery_visible=gallery_visible)
            # Allow fine-grained filtering of how many stations
            #   or any other attribute in the URL params
            # Example: ?station_count__lte=10&activitylog__user=1
            MAPS_PER_PAGE = int(request.GET.get('per_page', 25))
            filters = {k: v for k, v in request.GET.items() if k not in NON_FILTERABLE}
            if filters:
                visible_maps = visible_maps.filter(**filters).distinct()
            # Add per_page and order_by to filters so they persist through pagination
            # Awkward structure but I don't care to put order_by=-id in the URL every time
                #   when I'm not specifying the order
            if request.GET.get('per_page'):
                filters['per_page'] = MAPS_PER_PAGE
            if request.GET.get('order_by'):
                filters['order_by'] = request.GET.get('order_by')

        if kwargs.get('tag') == 'notags':
            visible_maps = visible_maps.filter(tags__exact=None)
        elif kwargs.get('tag') == 'named':
            visible_maps = visible_maps.exclude(name__exact='')
        elif kwargs.get('tag') == 'thumbnail':
            # Return all the ones with thumbnails, which will allow me to quickly
            #   regenerate any thumbnails if I make changes to the rendering
            visible_maps = visible_maps.exclude(thumbnail__exact='')
        elif kwargs.get('tag') in [t.slug for t in tags]:
            visible_maps = visible_maps.filter(tags__slug=kwargs.get('tag'))

        order_by = request.GET.get('order_by', '-id')
        visible_maps = visible_maps.prefetch_related('tags').order_by(order_by)

        paginator = Paginator(visible_maps, MAPS_PER_PAGE)

        page = request.GET.get('page')
        try:
            saved_maps = paginator.get_page(page)
        except PageNotAnInteger:
            saved_maps = paginator.get_page(1)
        except EmptyPage:
            saved_maps = paginator.get_page(paginator.num_pages)

        context = {
            'args': filters,
            'saved_maps': saved_maps,
            'maps_total': visible_maps.count(),
            'tags': tags,
            'is_staff': request.user.is_staff,
            'permissions': {
                'hide_map': request.user.has_perm('map_saver.hide_map'),
                'name_map': request.user.has_perm('map_saver.name_map'),
                'tag_map': request.user.has_perm('map_saver.tag_map'),
                'generate_thumbnail': request.user.has_perm('map_saver.generate_thumbnail'),
            }
        }

        return render(request, 'MapGalleryView.html', context)

def load_map_data(saved_map):

    """ Returns a JSON object of a saved_map's mapdata
    """

    return json.loads(
                str(
                    json.loads(
                        json.dumps(
                            saved_map.mapdata.replace("u'", "'").replace("'", '"').replace("\\", "").strip('"').strip("'")
                        )
                    )
                )
            )

class MapSimilarView(TemplateView):

    """ Get: Display a gallery of maps that are similar to the specified map.
             This is helpful for quickly browsing maps that are similar to the specified map
                and hopefully hiding ones that are too similar / older versions.

        Since this is so computationally taxing, it's important that this is available
            only to site admins.
            ^ Since moving to only checking by station names, performance is improved
                but I'm going to keep the login_required designation

        2018-12: Performance is deteriorating as the number of maps it needs to scan grows.
            Reduce the search space so that it only compares against maps
            1. that are actually in the public gallery
            2. or have not been reviewed yet

        2019-07: Reducing the search space even further by using the pre-calculated
                 station_count attribute and filtering by a small threshold +/- that
    """

    @method_decorator(gzip_page)
    @method_decorator(login_required)
    def get(self, request, **kwargs):

        # Filter by +/- 20% of the current map's number of stations instead of all visible maps
        STATION_THRESHOLD = 0.2
        similar_maps = []
        similarity_scores = {}
        urlhash_to_map = {} # this is so I can access the map object once it has been sorted by similarity
        tags = Tag.objects.all().order_by('id')

        try:
            this_map = SavedMap.objects.prefetch_related('tags').get(urlhash=kwargs.get('urlhash'))
        except ObjectDoesNotExist:
            pass
        except MultipleObjectsReturned:
            # This should never happen, but it happened once?
            this_map = SavedMap.objects.prefetch_related('tags').filter(urlhash=kwargs.get('urlhash')).order_by('id')[0]
        else:

            this_map_stations_lower_bound = this_map.station_count * (1 - STATION_THRESHOLD)
            this_map_stations_upper_bound = this_map.station_count * (1 + STATION_THRESHOLD)

            visible_maps = SavedMap.objects.filter(gallery_visible=True).filter(tags__exact=None) \
                .exclude(station_count__lt=this_map_stations_lower_bound) \
                .exclude(station_count__gt=this_map_stations_upper_bound)
            gallery_maps = SavedMap.objects.filter(gallery_visible=True) \
                .exclude(thumbnail__exact='') \
                .exclude(name__exact='') \
                .exclude(tags__slug='reviewed') \
                .exclude(station_count__lt=this_map_stations_lower_bound) \
                .exclude(station_count__gt=this_map_stations_upper_bound)
            visible_maps = visible_maps | gallery_maps # merge these querysets
            visible_maps = visible_maps.prefetch_related('tags').order_by('id').distinct()

            this_map_stations = set(this_map.stations.split(','))

            for one_map in visible_maps:
                if one_map.id == this_map.id:
                    # Comparing a map to itself would be a perfect match.
                    #   So don't do it.
                    continue
                else:
                    try:
                        one_map_stations = set(one_map.stations.split(','))
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

            similar_maps.sort(key=lambda similarity_scores: similarity_scores.urlhash, reverse=True)

            # It's easier to compare the maps if I can also see the base map on the similarity page
            similar_maps.insert(0, this_map)

        context = {
            'headline': '{0} Maps similar to {1}'.format(len(similar_maps) - 1, kwargs.get('urlhash')),
            'saved_maps': similar_maps,
            'similarity_scores': similarity_scores,
            'tags': tags,
            'is_staff': request.user.is_staff,
            'permissions': {
                'hide_map': request.user.has_perm('map_saver.hide_map'),
                'name_map': request.user.has_perm('map_saver.name_map'),
                'tag_map': request.user.has_perm('map_saver.tag_map'),
                'generate_thumbnail': request.user.has_perm('map_saver.generate_thumbnail'),
            }
        }

        return render(request, 'MapGalleryView.html', context)

class CreatorNameMapView(TemplateView):

    # @method_decorator(csrf_exempt) # Break glass in case of CSRF failure
    @method_decorator(never_cache)
    def post(self, request, **kwargs):

        """ Allow creators to name / "tag" their maps
            (but not after I've named them)
            Also prevent subsequent visitors from naming the maps
        """

        name = request.POST.get('name')
        tags = request.POST.get('tags')
        naming_token = request.POST.get('naming_token')
        context = {'saved_map': ''}

        if name or tags:
            try:
                this_map = SavedMap.objects.get(urlhash=request.POST.get('urlhash'))
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                pass
            else:
                if this_map.naming_token and this_map.naming_token == naming_token:
                    # This is the original creator of the map; allow them to name the map.
                    this_map.name = sanitize_string(f'{name} ({tags})' if tags in ALLOWED_TAGS else f'{name}')[:255]
                    this_map.save()
                    context['saved_map'] = 'Success'
                else:
                    # Either I have renamed this map,
                    #   or someone is trying to be sneaky
                    # Naming this map is no longer an option for the end user.
                    pass

        return render(request, 'MapDataView.html', context)


class MapAdminActionView(TemplateView):

    @method_decorator(login_required)
    def post(self, request, **kwargs):

        """ Perform an administrator action on a map
        """

        ALLOWED_ACTIONS = (
            'hide',
            'addtag',
            'removetag',
            'thumbnail',
            'image',
            'name',
            'publish',
        )
        context = {}

        action = request.POST.get('action')

        if action in ALLOWED_ACTIONS and request.POST.get('map'):
            try:
                this_map = SavedMap.objects.get(id=request.POST.get('map'))
            except ObjectDoesNotExist:
                context['status'] = '[ERROR] Map does not exist.'
            else:
                if this_map.publicly_visible and not request.user.has_perm('map_saver.edit_publicly_visible'):
                    raise PermissionDenied
                if action == 'hide' and request.user.has_perm('map_saver.hide_map'):
                    if this_map.gallery_visible:
                        this_map.gallery_visible = False
                    else:
                        this_map.gallery_visible = True
                    this_map.save()
                elif action in ('addtag', 'removetag') and request.user.has_perm('map_saver.tag_map'):
                    tag = request.POST.get('tag')
                    try:
                        # Only use existing tags; explicitly use slug intead of name
                        # This fixes the problem where 'favorite' wouldn't duplicate on .add()
                        #   but 'needs-review' would
                        tag = Tag.objects.get(slug=tag)
                    except ObjectDoesNotExist:
                        pass
                    else:
                        if tag:
                            if action == 'addtag':
                                this_map.tags.add(tag)
                            elif action == 'removetag':
                                this_map.tags.remove(tag)
                            this_map.save()
                elif action == 'thumbnail' and request.user.has_perm('map_saver.generate_thumbnail'):
                    this_map.thumbnail = request.POST.get('data', '')
                    this_map.save()
                elif action == 'image' and request.user.is_superuser:
                    data = request.POST.get('data')
                    with open(os.path.join(settings.STATIC_ROOT, 'images/') + f"{this_map.urlhash}.png", "wb") as image_file:
                        image_file.write(base64.b64decode(data[22:]))
                elif action == 'name' and request.user.has_perm('map_saver.name_map'):
                    name = request.POST.get('name')
                    this_map.name = name
                    this_map.naming_token = '' # This map can no longer be named by the end user
                    this_map.save()
                elif action == 'publish' and request.user.has_perm('map_saver.generate_thumbnail'):
                    this_map.publicly_visible = not this_map.publicly_visible
                    this_map.save()
                else:
                    raise PermissionDenied
                context['status'] = 'Success'
                activity_details = request.POST.get('tag') or request.POST.get('name') or request.POST.get('data', '')[:21]
                if action == 'hide' and this_map.gallery_visible:
                    action = 'show'
                ActivityLog.objects.create(
                    user=request.user,
                    savedmap=this_map,
                    action=action,
                    details=activity_details,
                )
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
                                    metro_map.mapdata.replace("u'", "'").replace("'", '"').replace("\\", "").strip('"').strip("'")
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

    @method_decorator(cache_page(60 * 60 * 24 * 30))
    @method_decorator(gzip_page)
    def get(self, request, **kwargs):
        urlhash = kwargs.get('urlhash')

        context = {}

        try:
            saved_map = SavedMap.objects.get(urlhash=urlhash)
        except ObjectDoesNotExist:
            context['error'] = '[ERROR] The requested map does not exist ({0})'.format(urlhash)
        except MultipleObjectsReturned:
            saved_map = SavedMap.objects.filter(urlhash=urlhash).earliest('id')

        if not context.get('error'):
            if saved_map.data:
                mapdata = json.dumps(saved_map.data)
            elif saved_map.mapdata:
                mapdata = saved_map.mapdata
            else:
                mapdata = {}
            context['saved_map'] = mapdata

        return render(request, 'MapDataView.html', context)

    # @method_decorator(csrf_exempt) # Break glass in case of CSRF failure
    @method_decorator(never_cache)
    def post(self, request, **kwargs):
        mapdata = request.POST.get('metroMap')

        context = {}

        form = CreateMapForm({'mapdata': mapdata})
        if form.is_valid():
            mapdata = form.cleaned_data['mapdata']
            urlhash = form.cleaned_data['urlhash']
            naming_token = form.cleaned_data['naming_token']
            data_version = form.cleaned_data['data_version']
            try:
                # Doesn't override the saved map if it already exists.
                saved_map = SavedMap.objects.only('urlhash').get(urlhash=urlhash)
                context['saved_map'] = f'{urlhash},'
            except ObjectDoesNotExist:
                if data_version == 2:
                    saved_map = SavedMap.objects.create(**{
                        'urlhash': urlhash,
                        'data': mapdata,
                        'naming_token': naming_token,
                    })
                else:
                    saved_map = SavedMap.objects.create(**{
                        'urlhash': urlhash,
                        'mapdata': json.dumps(mapdata),
                        'naming_token': naming_token,
                    })
                context['saved_map'] = f'{urlhash},{naming_token}'
            except MultipleObjectsReturned:
                # This should never happen, but it happened once
                # Perhaps this was due to a race condition?
                context['saved_map'] = f'{urlhash},'
        else:
            # Anything that appears before the first colon will be internal-only;
            #   everything else is user-facing.
            errors = form.errors.get('mapdata', [])
            errors = '[ERROR] {0}'.format(' '.join(str(errors).split(':')[1:]).split('</')[0])
            context['error'] = errors
            logger.error('[ERROR] [FAILEDVALIDATION] ({0}); mapdata: {1}'.format(errors, mapdata))

        return render(request, 'MapDataView.html', context)


class AdminHomeView(TemplateView):

    """ A sort of 'home base' for admins like me
        to review important stats centrally
        and serve as a dashboard for all of the main reviewing tasks
    """

    template_name = 'AdminHome.html'

    @method_decorator(staff_member_required)
    def get(self, request, **kwargs):
        return super().get(request, **kwargs)

    @method_decorator(staff_member_required)
    def post(self, request, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied

        action = request.POST.get('action')
        if action == 'mass_hide':
            group = request.POST.get('group', '').replace("'", '"')
            group = json.loads(group)
            maps = SavedMap.objects.filter(
                gallery_visible=True,
                tags__exact=None,
                **group,
            )
            maps.update(gallery_visible=False)

        # Return empty response for success
        return render(request, 'MapDataView.html', {})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get basic usage stats of number of maps created
        eastern_time = pytz.timezone('US/Eastern')
        today = datetime.datetime.now(tz=eastern_time).date()
        yesterday = today - datetime.timedelta(days=1)
        last_30 = today - datetime.timedelta(days=30)
        last_90 = today - datetime.timedelta(days=90)
        prev_90_start = today - datetime.timedelta(days=180)
        prev_90_end = today - datetime.timedelta(days=91)

        context['today'] = today
        context['yesterday'] = yesterday

        context['created_today'] = SavedMap.objects.filter(created_at=today).count()
        context['created_yesterday'] = SavedMap.objects.filter(created_at=yesterday).count()
        context['last_30'] = SavedMap.objects.filter(created_at__gt=last_30).count()
        context['last_90'] = SavedMap.objects.filter(created_at__gt=last_90).count()
        context['prev_90'] = SavedMap.objects.filter(
            created_at__gt=prev_90_start,
            created_at__lte=prev_90_end,
        ).count()
        context['last_90_change'] = context['last_90'] - context['prev_90']

        # Get numbers of maps needing review
        filter_groups = {
            '0 stations': {'station_count': 0},
            '1-10 stations': {'station_count__gte': 1, 'station_count__lte': 10},
            '11-20 stations': {'station_count__gte': 11, 'station_count__lte': 20},
            '21-30 stations': {'station_count__gte': 21, 'station_count__lte': 30},
            '31-40 stations': {'station_count__gte': 31, 'station_count__lte': 40},
            '41-50 stations': {'station_count__gte': 41, 'station_count__lte': 50},
            '51-75 stations': {'station_count__gte': 51, 'station_count__lte': 75},
            '76-100 stations': {'station_count__gte': 76, 'station_count__lte': 100},
            '101-200 stations': {'station_count__gte': 101, 'station_count__lte': 200},
            '201-500 stations': {'station_count__gte': 201, 'station_count__lte': 500},
            '501+ stations': {'station_count__gte': 501},
        }

        maps_needing_review = SavedMap.objects.filter(tags__exact=None, gallery_visible=True)

        PER_PAGE = 100

        context['maps'] = {
            group: {
                'needing_review': maps_needing_review.filter(**filters).count(),
                'total': SavedMap.objects.filter(**filters).count(),
                'review_link': '/admin/gallery/notags/?per_page={0}&{1}'.format(
                    PER_PAGE,
                    urllib.parse.urlencode(filters)
                ),
                'filters': filters,
            } for group, filters in filter_groups.items()
        }

        context['totals'] = {
            'needing_review': maps_needing_review.count(),
            'total': SavedMap.objects.count(),
        }

        maps_tagged_need_review = SavedMap.objects.filter(
            tags__slug='needs-review',
            gallery_visible=True,
        ).count()
        maps_no_tags = SavedMap.objects.filter(
            tags__exact=None,
            gallery_visible=True,
        ).count()

        context['maps_no_tags'] = maps_no_tags
        context['maps_tagged_need_review'] = maps_tagged_need_review

        # How many travel systems do we have a publicly visible real/speculative map for?
        travel_system_names = [ts.name.split(',')[0] for ts in TravelSystem.objects.all()]
        travel_system_has_real_map = set()
        maps_tagged_real = SavedMap.objects.filter(
            tags__slug='real',
            publicly_visible=True,
        )

        travel_system_has_speculative_map = set()
        maps_tagged_speculative = SavedMap.objects.filter(
            tags__slug='speculative',
            publicly_visible=True,
        )

        # Note: even though I have a stored field for suggested_city,
        # it's still valuable to check the calculated value below
        # since I'm overriding the overlap parameter
        for real_map in maps_tagged_real:
            if real_map.name in travel_system_names or \
            real_map.suggested_city in travel_system_names or \
            real_map._suggest_city(overlap=int(real_map.station_count * 0.8)):
                travel_system_has_real_map.add(real_map.name)

        for speculative_map in maps_tagged_speculative:
            if speculative_map.name in travel_system_names or \
            speculative_map.suggested_city in travel_system_names or \
            speculative_map._suggest_city(overlap=int(speculative_map.station_count * 0.4)):
                travel_system_has_speculative_map.add(speculative_map.name)

        travel_system_names = set(travel_system_names)

        context['travel_system_has_real_map'] = sorted(travel_system_has_real_map)
        context['travel_system_missing_real_map'] = sorted(
            travel_system_names - travel_system_has_real_map
        )
        context['travel_system_has_speculative_map'] = sorted(travel_system_has_speculative_map)
        context['travel_system_missing_speculative_map'] = sorted(
            travel_system_names - travel_system_has_speculative_map
        )
        context['total_travel_systems'] = TravelSystem.objects.count()

        # Maps currently in the public gallery
        public_tags = ['real', 'speculative', 'unknown', 'favorite']
        public_tags = {tag: {} for tag in public_tags}
        context['public_tags'] = {}
        public = SavedMap.objects.filter(publicly_visible=True)
        for tag in public_tags:
            context['public_tags'][tag] = public.filter(tags__slug=tag).count()
        context['public_total'] = public.count()

        context['most_popular_cities'] = SavedMap.objects.exclude(suggested_city='') \
            .values_list('suggested_city') \
            .annotate(city_count=Count('suggested_city')) \
            .order_by('-city_count')[:10]

        context['most_popular_cities_by_name'] = SavedMap.objects.exclude(name='') \
            .filter(publicly_visible=True) \
            .values_list('name') \
            .annotate(city_count=Count('name')) \
            .order_by('-city_count')[:10]

        return context


class MapsByDateView(TemplateView):

    def grouping(self, date, group_by):

        """ Helper function to return a set of maps grouped by their date type
        """

        if group_by == 'day':
            return date['created_at'].strftime('%Y-%m-%d')
        elif group_by == 'month':
            return date['created_at'].strftime('%Y-%m')
        elif group_by == 'week':
            return date['created_at'].strftime('%YW%W')
        elif group_by == 'weekday':
            return date['created_at'].strftime('%w')

    @method_decorator(staff_member_required)
    def get(self, request, **kwargs):
        context = {}
        return render(request, 'MapsByDateView.html', context)

    @method_decorator(staff_member_required)
    def post(self, request, **kwargs):

        """ Creates a Javascript object of the number of maps created by date.
            Example: { "2018-09-18": 34, "2018-04-11": 471 }
        """

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        group_by = request.POST.get('group_by[]', 'day')
        include_visible = request.POST.get('visible')

        # I can't just use the optional second parameter of .get()
        #   because otherwise .strptime() will fail
        if start_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = datetime.datetime.today() - \
            datetime.timedelta(days=30)

        if end_date:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = datetime.datetime.today()

        number_of_days = abs((end_date - start_date).days)

        saved_maps_by_date = SavedMap.objects.filter(
            created_at__lte=end_date,
            created_at__gt=start_date
        )

        maps_count = saved_maps_by_date.count()

        saved_maps_by_date = saved_maps_by_date.values('created_at').annotate(count=Count('id'))

        if include_visible:
            gallery_visible_maps_by_date = SavedMap.objects.filter(
                created_at__lte=end_date,
                created_at__gt=start_date,
                gallery_visible=True,
            ).values('created_at').annotate(count=Count('id'))

            visible_maps_by_date = {}
            for date in gallery_visible_maps_by_date:
                grouping = self.grouping(date, group_by)
                if visible_maps_by_date.get(grouping):
                    visible_maps_by_date[grouping] += date['count']
                else:
                    visible_maps_by_date[grouping] = date['count']

        maps_by_date = {}
        for date in saved_maps_by_date:
            grouping = self.grouping(date, group_by)
            if maps_by_date.get(grouping):
                maps_by_date[grouping] += date['count']
            else:
                maps_by_date[grouping] = date['count']

        context = {
            "maps_by_date": maps_by_date,
            "maps_count": maps_count,
            "visible_maps_by_date": visible_maps_by_date if include_visible else [],
            "number_of_days": number_of_days,
            "start_date": start_date,
            "end_date": end_date,
        }

        return render(request, 'MapsByDateView.json', context)

class MapsPerDayView(DayArchiveView):

    """ Display the maps created this day
    """

    queryset = SavedMap.objects.defer(*SavedMap.DEFER_FIELDS).all().exclude(tags__slug='calendar-hidden')
    date_field = 'created_at'
    paginate_by = 50
    context_object_name = 'maps'
    allow_empty = True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        FIRST_YEAR = 2017
        context['all_years'] = range(datetime.datetime.now().year, (FIRST_YEAR - 1), -1)

        if context['day'] < datetime.date(2018, 9, 13):
            context['date_estimate_disclaimer'] = True

        if context['day'] <= datetime.date(2017, 9, 6):
            context['previous_day'] = False

        return context

    @method_decorator(cache_control(max_age=60))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class SameDayView(ListView):

    """ Show all maps created on the same day as a given URLhash,
            which can be especially useful for finding prior versions of the same map
    """

    model = SavedMap
    context_object_name = 'maps'

    def get_queryset(self):
        urlhash = self.request.path_info.split('/')[-1]
        this_map = get_object_or_404(SavedMap, urlhash=urlhash)

        # I'd use __date here, but then SQL won't use the index on created_at
        return super().get_queryset().defer(*SavedMap.DEFER_FIELDS).filter(
            created_at__gte=this_map.created_at.date(),
            created_at__lt=this_map.created_at.date() + datetime.timedelta(days=1),
        )

class RecaptchaMixin:

    def is_submission_valid(self, form):

        """ Check whether the submitted form was done by a human
        """

        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': form.cleaned_data['g-recaptcha-response'],
                },
            ).json()
        except Exception as exc:
            pass
        else:
            try:
                is_valid = response.get('success')
                captcha = response.get('score', 0)
                captcha = float(captcha)
            except Exception as exc:
                captcha = 0
            return (is_valid and captcha > settings.RECAPTCHA_VALID_THRESHOLD)

class IdentifyMapView(RecaptchaMixin, FormView):
    model = IdentifyMap
    form_class = IdentifyForm
    fields = ['name', 'map_type']

    def get_success_url(self, urlhash):
        return reverse_lazy('rate', args=(urlhash, ))

    def form_valid(self, form):
        try:
            urlhash = form.cleaned_data['urlhash']
            name = form.cleaned_data['name']
            map_type = form.cleaned_data['map_type']
            mmap = SavedMap.objects.filter(urlhash=urlhash).first()
            is_submission_valid = self.is_submission_valid(form)
        except Exception as exc:
            pass
        else:
            if is_submission_valid:
                self.model.objects.create(
                    saved_map=mmap,
                    name=name,
                    map_type=map_type,
                )
                already_identified = self.request.session.get('identified', [])
                self.request.session['identified'] = already_identified + [mmap.id]

        return HttpResponseRedirect(self.get_success_url(urlhash))

    def form_invalid(self, form):
        urlhash = form.cleaned_data['urlhash']
        return HttpResponseRedirect(self.get_success_url(urlhash))

    def get(self, request, *args, **kwargs):
        urlhash = kwargs.get('urlhash')
        return HttpResponseRedirect(self.get_success_url(urlhash))


class RateMapView(RecaptchaMixin, FormView, DetailView):
    model = SavedMap
    context_object_name = 'map'
    slug_field = 'urlhash'
    slug_url_kwarg = 'urlhash'
    template_name = 'map_saver/savedmap_rate.html'

    form_class = RateForm

    def get_success_url(self, urlhash):
        return reverse_lazy('rate', args=(urlhash, ))

    @method_decorator(cache_control(max_age=60))
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except MultipleObjectsReturned:
            self.object = SavedMap.objects.filter(urlhash=kwargs.get('urlhash')).earliest('id')
        context = self.get_context_data(object=self.object, map=self.object)
        if not self.object.id in request.session.get('rated', []):
            context['form_like'] = self.form_class(dict(urlhash=self.object.urlhash, choice='likes'))
            context['form_dislike'] = self.form_class(dict(urlhash=self.object.urlhash, choice='dislikes'))
        if not self.object.id in request.session.get('identified', []):
            context['identify_form'] = IdentifyForm(dict(urlhash=self.object.urlhash))

        return self.render_to_response(context)

    def form_valid(self, form):
        try:
            urlhash = form.cleaned_data['urlhash']
            choice = form.cleaned_data['choice']
            assert choice in ('likes', 'dislikes')
            mmap = SavedMap.objects.filter(urlhash=urlhash)
            is_submission_valid = self.is_submission_valid(form)
        except Exception as exc:
            pass
        else:
            if is_submission_valid:
                mmap.update(**{choice: F(choice) + 1})
                already_rated = self.request.session.get('rated', [])
                self.request.session['rated'] = already_rated + [mmap.first().id]

        return HttpResponseRedirect(self.get_success_url(urlhash))

    def form_invalid(self, form):
        urlhash = form.cleaned_data['urlhash']
        return HttpResponseRedirect(self.get_success_url(urlhash))

class RandomMapView(RateMapView):
    model = SavedMap
    context_object_name = 'map'
    template_name = 'map_saver/savedmap_rate.html'

    @method_decorator(never_cache)
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        pks = SavedMap.objects.all().values_list('pk', flat=True)
        return SavedMap.objects.get(pk=random.choice(pks))


class HighestRatedMapsView(ListView):
    model = SavedMap
    paginate_by = 100
    context_object_name = 'maps'

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            likes__gt=0,
        ).defer(*SavedMap.DEFER_FIELDS).order_by('-likes')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['showing_best'] = True
        return context


class CreditsView(TemplateView):
    template_name = 'credits.html'

class HelpView(TemplateView):
    template_name = 'help.html'

