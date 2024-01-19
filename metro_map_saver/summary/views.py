from django.shortcuts import render, reverse
from django.views.generic.dates import (
    YearArchiveView,
    MonthArchiveView,
    WeekArchiveView,
    DayArchiveView,
)

from summary.models import MapsByDay

import calendar
import datetime


class MapHTMLCalendar(calendar.HTMLCalendar):

    """ Generates an HTMLCalendar useful for displaying counts of maps created.
    """

    cssclasses = [
        default_style + " map-calendar-day"
        for default_style in
        calendar.HTMLCalendar.cssclasses
    ]
    cssclasses_weekday_head = [
        default_style + " map-calendar-weekday"
        for default_style in
        calendar.HTMLCalendar.cssclasses
    ]
    cssclass_month_head = 'map-calendar-month styling-redline bg-styled p-3'
    cssclass_month = 'map-calendar w-100 mt-3 mb-3 text-center'
    cssclass_noday = 'noday map-calendar-day'

    def formatmonthname(self, theyear, themonth, withyear=True):

        """ Overrides to include the number of maps created this month
        """

        monthname = super().formatmonthname(theyear, themonth, withyear)

        return monthname.replace('</th></tr>', f'''
            ({self.maps_count:,} maps)</th></tr>
        ''')


    def formatday(self, day, weekday):

        """ Overrides built-in to include the maps for this day
        """

        if day == 0:
            # day outside month
            return '<td class="%s">&nbsp;</td>' % self.cssclass_noday
        else:
            link = self.maps_by_day.get(day, {}).get('date', '') or ''
            if link:
                link = reverse('calendar-day', kwargs={
                    'year': link.year,
                    'month': link.month,
                    'day': link.day,
                })
                return f'''
                    <td class="{self.cssclasses[weekday]} day-{day}">
                        <div class="map-calendar-day-mark">
                            <a href="{link}">{day}</a>
                        </div>
                        <div class="map-calendar-data p-1 m-1">
                            <h1><a href="{link}">
                                {self.maps_by_day.get(day, {}).get('count', '')}
                            </a></h1>
                        </div>
                    </td>
                '''
            else:
                return f'''
                    <td class="{self.cssclasses[weekday]} day-{day}">
                        <div class="map-calendar-day-mark">
                            {day}
                        </div>
                        <div class="map-calendar-data p-1 m-1"></div>
                    </td>
                '''

    def weekly_calendar(self, theyear, themonth, theweek, withyear=True):

        """ Return a formatted week, even across month boundaries
        """

        html = [
            f'<table border="0" cellpadding="0" cellspacing="0" class="{self.cssclass_month}">',
            self.formatmonthname(theyear, themonth, withyear=withyear),
            self.formatweekheader(),
            self.formatweek(theweek),
            '</table>',
        ]

        return '\n'.join(html)


class MapsByDateMixin:
    queryset = MapsByDay.objects.all()
    date_field = 'day'
    context_object_name = 'maps'

    def group_maps_by_day(self, maps):

        """ Map counts by their day for inclusion in the calendar
        """

        maps_by_day = {}
        if isinstance(self, MonthArchiveView) and maps.count() < self.days_this_month:
            # Some months don't have a map every day, so adjust it.
            maps_original = [m for m in maps] # Evaluate the queryset
            days_with_maps = [m.day.day for m in maps_original]

            adjusted_maps = []
            for day in range(1, self.days_this_month + 1):
                if day not in days_with_maps:
                    adjusted_maps.append(None)
                else:
                    adjusted_maps.append(maps_original.pop(0))
            maps = adjusted_maps
        elif isinstance(self, WeekArchiveView) and maps.count() < 7:
            # Some weeks don't have a map every day, so adjust it.
            maps_original = [m for m in maps]
            days_with_maps = [m.day.day for m in maps_original]

            adjusted_maps = []
            for day in self.days_this_week:
                if day not in days_with_maps:
                    adjusted_maps.append(None)
                else:
                    adjusted_maps.append(maps_original.pop(0))
            maps = adjusted_maps

        if isinstance(self, MonthArchiveView):
            for index, m in enumerate(maps):
                maps_by_day[index + 1] = {
                    'count': getattr(m, 'maps', 0),
                    'date': getattr(m, 'day', None),
                }
        elif isinstance(self, WeekArchiveView):
            for index, m in enumerate(maps):
                which_day = getattr(m, 'day', None)
                if which_day:
                    which_day = which_day.day
                else:
                    which_day = index + 1
                maps_by_day[which_day] = {
                    'count': getattr(m, 'maps', 0),
                    'date': getattr(m, 'day', None),
                }

        return maps_by_day


    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['maps'] = context['maps'].order_by('day')

        html_calendar = MapHTMLCalendar()
        html_calendar.setfirstweekday(calendar.MONDAY)
        html_calendar.maps_by_day = self.group_maps_by_day(context['maps'])
        html_calendar.maps_count = sum([mbd['count'] for mbd in html_calendar.maps_by_day.values() if mbd])
        context['maps_count'] = html_calendar.maps_count
        context['calendar'] = html_calendar

        return context

class MapsPerYearView(MapsByDateMixin, YearArchiveView):
    # Since it's not actually the maps, only the MapsByDay objects, this is fine
    make_object_list = True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        months = {m: 0 for m in range(1, 13)}
        for maps_by_day in context['maps']:
            months[maps_by_day.day.month] += maps_by_day.maps

        year = kwargs['year'].year

        # I'd rather use a dictionary for map_count_by_month as it's more straightforward,
        #   but I need to be able to group by month with regroup,
        #   and need to be able to use forloop.counter0 (I'd prefer .grouper|date:'n')
        #   to access the correct month for map_count_by_month.
        # This also has the side effect of needing a separate variable for the URLs
        # Otherwise months without any maps will lead to others displaying erroneous sums
        context['month_header_links'] = [datetime.date(year, k, 1) for k, v in months.items() if v > 0]
        context['map_count_by_month'] = [v for v in months.values() if v > 0]

        context['map_count_this_year'] = sum(context['map_count_by_month'])

        return context

class MapsPerMonthView(MapsByDateMixin, MonthArchiveView):

    def get_context_data(self, *args, **kwargs):
        year, month = kwargs['month'].year, kwargs['month'].month
        self.days_this_month = calendar.monthrange(year, month)[1]

        context = super().get_context_data(*args, **kwargs)

        context['calendar'] = context['calendar'].formatmonth(
            year,
            month,
            withyear=True,
        )

        return context

class MapsPerWeekView(MapsByDateMixin, WeekArchiveView):
    week_format = '%V'

    def get_context_data(self, *args, **kwargs):
        year = kwargs['week'].year
        month = kwargs['week'].month
        week = int(kwargs['week'].strftime('%V'))

        monday_of_week = datetime.datetime.strptime(f'{year}-{week}-1', '%G-%V-%u')
        days_wanted = []
        for offset in range(0, 7):
            day = monday_of_week + datetime.timedelta(days=offset)
            days_wanted.append((day.day, day.weekday()))

        self.days_this_week = [d[0] for d in days_wanted]

        context = super().get_context_data(*args, **kwargs)
        context['calendar'].this_week_only = week
        context['calendar'] = context['calendar'].weekly_calendar(
            year,
            month,
            days_wanted,
        )

        return context

class MapsPerDayView(MapsByDateMixin, DayArchiveView):
    pass
