
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, PermissionDenied
from django.db.models import Count
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.gzip import gzip_page

import datetime
import difflib
import hashlib
import json
import logging
import pprint
import random
import urllib.parse

from taggit.models import Tag

from moderate.models import ActivityLog
from .models import SavedMap
from .validator import is_hex, sanitize_string, validate_metro_map, hex64

logger = logging.getLogger(__name__)

class HomeView(TemplateView):

    template_name = 'index.html'

    @method_decorator(gzip_page)
    def get(self, request, **kwargs):
        if not request.GET.get('map'):
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
                saved_map = SavedMap.objects.get(urlhash=request.GET.get('map'))
            except Exception:
                context = {}
            else:
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

        return render(request, self.template_name, context)


class PublicGalleryView(TemplateView):

    template_name = 'PublicGallery.html'

    @method_decorator(gzip_page)
    def get(self, request, **kwargs):

        tags = [
            'favorite',
            'real',
            'speculative',
            'unknown',
        ]

        thumbnails = SavedMap.objects \
            .filter(gallery_visible=True) \
            .exclude(thumbnail__exact='') \
            .exclude(name__exact='') \
            .exclude(tags__slug='reviewed')

        context = {tag:thumbnails.filter(tags__slug=tag).order_by('name') for tag in tags}
        context['favorite'] = context['favorite'].order_by('?')[:8]

        return render(request, self.template_name, context)

class ThumbnailGalleryView(TemplateView):

    @method_decorator(gzip_page)
    def get(self, request, **kwargs):

        thumbnails = SavedMap.objects \
            .filter(gallery_visible=True) \
            .exclude(thumbnail__exact='') \
            .exclude(name__exact='') \
            .exclude(tags__slug='reviewed')

        if kwargs.get('tag'):
            thumbnails = thumbnails.filter(tags__slug=kwargs.get('tag'))

        if kwargs.get('tag') == 'favorite':
            thumbnails = thumbnails.order_by('?')[:8]
        else:
            thumbnails = thumbnails.order_by('name')

        context = {
            'thumbnails': thumbnails.values('thumbnail', 'name', 'urlhash')
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
                # Add per_page to filters so it persists through pagination
                filters['per_page'] = MAPS_PER_PAGE

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

        visible_maps = visible_maps.prefetch_related('tags').order_by('-id')

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

def get_stations(mapdata):

    """ Returns a set of station names from a given mapdata
    """

    stations = set()

    for x in mapdata:
        for y in mapdata[x]:
            stations.add(mapdata[x][y].get('station', {}).get('name', ''))

    return stations

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

        try:
            this_map = SavedMap.objects.prefetch_related('tags').get(urlhash=kwargs.get('urlhash'))
        except ObjectDoesNotExist:
            similar_maps = []
            similarity_scores = {}
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
            visible_maps = visible_maps.prefetch_related('tags').order_by('id')
            tags = Tag.objects.all().order_by('id')

            this_map_stations = set(this_map.stations.split(','))

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
                    this_map.name = f'{name} ({tags})' if tags else f'{name}'
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
            'name',
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
                    if tag:
                        if action == 'addtag':
                            this_map.tags.add(tag)
                        elif action == 'removetag':
                            this_map.tags.remove(tag)
                        this_map.save()
                elif action == 'thumbnail' and request.user.has_perm('map_saver.generate_thumbnail'):
                    this_map.thumbnail = request.POST.get('data', '')
                    this_map.save()
                elif action == 'name' and request.user.has_perm('map_saver.name_map'):
                    name = request.POST.get('name')
                    this_map.name = name
                    this_map.naming_token = '' # This map can no longer be named by the end user
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

    @method_decorator(gzip_page)
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
        except AssertionError as e:
            # Anything that appears before the first colon will be internal-only;
            #   everything else is user-facing.
            context['error'] = '[ERROR] {0}'.format(' '.join(str(e).split(':')[1:]))
            logger.error('[ERROR] [FAILEDVALIDATION] ({0}); mapdata: {1}'.format(e, mapdata))
        else:
            urlhash = hex64(hashlib.sha256(str(mapdata).encode('utf-8')).hexdigest()[:12])
            try:
                # Doesn't override the saved map if it already exists.
                saved_map = SavedMap.objects.get(urlhash=urlhash)
            except ObjectDoesNotExist:
                saved_map = SavedMap(**{
                    'urlhash': urlhash,
                    'mapdata': json.dumps(mapdata),
                    })
                saved_map.naming_token = hashlib.sha256('{0}'.format(random.randint(1, 100000)).encode('utf-8')).hexdigest()
                try:
                    saved_map.stations = ','.join(get_stations(mapdata)).lower()
                except Exception as e:
                    logger.error('[WARN] Failed to save stations for {0}: {1}'.format(urlhash, e))
                saved_map.save()
            except MultipleObjectsReturned:
                # This should never happen, but it happened once
                # Perhaps this was due to a race condition?
                saved_map = SavedMap.objects.filter(urlhash=urlhash)[0]

            context['saved_map'] = f'{saved_map.urlhash},{saved_map.naming_token}'

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get basic usage stats of number of maps created
        last_30 = datetime.datetime.today() - \
            datetime.timedelta(days=30)

        last_90 = datetime.datetime.today() - \
            datetime.timedelta(days=90)

        prev_90_start = datetime.datetime.today() - \
            datetime.timedelta(days=180)
        prev_90_end = datetime.datetime.today() - \
            datetime.timedelta(days=91)

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

        maps_needing_review = SavedMap.objects.filter(tags__exact=None).filter(gallery_visible=True)

        PER_PAGE = 100

        context['maps'] = {
            group: {
                'needing_review': maps_needing_review.filter(**filters).count(),
                'total': SavedMap.objects.filter(**filters).count(),
                'review_link': '/admin/gallery/notags/?per_page={0}&{1}'.format(
                    PER_PAGE,
                    urllib.parse.urlencode(filters)
                ),
            } for group, filters in filter_groups.items()
        }

        context['totals'] = {
            'needing_review': maps_needing_review.count(),
            'total': SavedMap.objects.count(),
        }

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
