
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
                .exclude(tags__name='reviewed') \
                .filter(tags__name='favorite') \
                .order_by('?')

            context = {
                'favorites': thumbnails[:3]
            }
        else:
            try:
                saved_map = SavedMap.objects.get(urlhash=request.GET.get('map'))
            except Exception:
                pass
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
            .exclude(tags__name='reviewed')

        context = {tag:thumbnails.filter(tags__name=tag).order_by('name') for tag in tags}
        context['favorite'] = context['favorite'].order_by('?')[:8]

        return render(request, self.template_name, context)

class ThumbnailGalleryView(TemplateView):

    @method_decorator(gzip_page)
    def get(self, request, **kwargs):

        thumbnails = SavedMap.objects \
            .filter(gallery_visible=True) \
            .exclude(thumbnail__exact='') \
            .exclude(name__exact='') \
            .exclude(tags__name='reviewed')

        if kwargs.get('tag'):
            thumbnails = thumbnails.filter(tags__name=kwargs.get('tag'))

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

        tags = Tag.objects.all().order_by('id')

        if request.GET.get('map') or kwargs.get('direct'):
            # Accessible either by
            #           /admin/direct/https://metromapmaker.com/?map=8RkQTRav
            #   or by   /admin/direct/8RkQTRav
            direct = request.GET.get('map', kwargs.get('direct', '')[-8:])
            visible_maps = SavedMap.objects.filter(urlhash=direct)
        else:
            visible_maps = SavedMap.objects.filter(gallery_visible=True)

        if kwargs.get('tag') == 'notags':
            visible_maps = visible_maps.filter(tags__exact=None)
        elif kwargs.get('tag') == 'named':
            visible_maps = visible_maps.exclude(name__exact='')
        elif kwargs.get('tag') == 'thumbnail':
            # Return all the ones with thumbnails, which will allow me to quickly
            #   regenerate any thumbnails if I make changes to the rendering
            visible_maps = visible_maps.exclude(thumbnail__exact='')
        elif kwargs.get('tag') in [t.name for t in tags]:
            visible_maps = visible_maps.filter(tags__name=kwargs.get('tag'))

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
    """

    @method_decorator(gzip_page)
    @method_decorator(login_required)
    def get(self, request, **kwargs):

        visible_maps = SavedMap.objects.filter(gallery_visible=True).filter(tags__exact=None)
        gallery_maps = SavedMap.objects.filter(gallery_visible=True) \
            .exclude(thumbnail__exact='') \
            .exclude(name__exact='') \
            .exclude(tags__name='reviewed')
        visible_maps = visible_maps | gallery_maps # merge these querysets
        visible_maps = visible_maps.prefetch_related('tags').order_by('id')
        tags = Tag.objects.all().order_by('id')

        try:
            this_map = SavedMap.objects.prefetch_related('tags').get(urlhash=kwargs.get('urlhash'))
        except ObjectDoesNotExist:
            similar_maps = []
            similarity_scores = {}
        else:

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

        if request.POST.get('action') in ALLOWED_ACTIONS and request.POST.get('map'):
            try:
                this_map = SavedMap.objects.get(id=request.POST.get('map'))
            except ObjectDoesNotExist:
                context['status'] = '[ERROR] Map does not exist.'
            else:
                if request.POST.get('action') == 'hide' and request.user.has_perm('map_saver.hide_map'):
                    if this_map.gallery_visible:
                        this_map.gallery_visible = False
                    else:
                        this_map.gallery_visible = True
                    this_map.save()
                elif request.POST.get('action') in ('addtag', 'removetag') and request.user.has_perm('map_saver.tag_map'):
                    tag = request.POST.get('tag')
                    if tag:
                        if request.POST.get('action') == 'addtag':
                            this_map.tags.add(tag)
                        elif request.POST.get('action') == 'removetag':
                            this_map.tags.remove(tag)
                        this_map.save()
                elif request.POST.get('action') == 'thumbnail' and request.user.has_perm('map_saver.generate_thumbnail'):
                    this_map.thumbnail = request.POST.get('data', '')
                    this_map.save()
                elif request.POST.get('action') == 'name' and request.user.has_perm('map_saver.name_map'):
                    name = request.POST.get('name')
                    this_map.name = name
                    this_map.naming_token = '' # This map can no longer be named by the end user
                    this_map.save()
                else:
                    raise PermissionDenied
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
            logging.error('[ERROR] [FAILEDVALIDATION] ({0}); mapdata: {1}'.format(e, mapdata))
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
                    logging.error('[WARN] Failed to save stations for {0}: {1}'.format(urlhash, e))
                saved_map.save()
            except MultipleObjectsReturned:
                # This should never happen, but it happened once
                # Perhaps this was due to a race condition?
                saved_map = SavedMap.objects.filter(urlhash=urlhash)[0]

            context['saved_map'] = f'{saved_map.urlhash},{saved_map.naming_token}'

        return render(request, 'MapDataView.html', context)




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
