"""metro_map_saver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.urls import include, path, re_path
from django.contrib import admin
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import cache_page, never_cache

import map_saver.views
import moderate.views
import summary.views

urlpatterns = [
    # Main page; only caches for 15 minutes so you don't have to wait a full day for static asset updates
    path('', cache_page(60 * 15)(map_saver.views.HomeView.as_view()), name='home'),

    # Public Gallery
    path('gallery/', map_saver.views.PublicGalleryView.as_view(), name='public_gallery'),

    # End-user actions (saving, loading, naming maps)
    path('save/', map_saver.views.MapDataView.as_view(), name='save_map'),
    path('load/<slug:urlhash>', map_saver.views.MapDataView.as_view(), name='load_map'),
    path('name/', map_saver.views.CreatorNameMapView.as_view(), name='name_map'),

    # Stats, using summary for performance
    path('calendar/<int:year>/', summary.views.MapsPerYearView.as_view(), name='calendar-year'),
    path('calendar/<int:year>/<int:month>/', summary.views.MapsPerMonthView.as_view(month_format='%m'), name='calendar-month'),
    path('calendar/<int:year>/week/<int:week>/', summary.views.MapsPerWeekView.as_view(year_format='%G', week_format='%V'), name='calendar-week'),

    path('calendar/<int:year>/<int:month>/<int:day>/', map_saver.views.MapsPerDayView.as_view(month_format='%m'), name='calendar-day'),

    # Admin HQ
    path('admin/home/', never_cache(map_saver.views.AdminHomeView.as_view()), name='admin_home'),

    # Admin Gallery
    re_path(r'admin/gallery/(?P<tag>[\w\-\_^\d]+)?/?$', never_cache(map_saver.views.MapGalleryView.as_view()), name='admin_gallery'),

    # Admin Gallery: Admin actions
    path('admin/action/', never_cache(map_saver.views.MapAdminActionView.as_view()), name='admin_action'),

    # Admin Gallery: Similar
    path('admin/similar/<slug:urlhash>', map_saver.views.MapSimilarView.as_view(), name='similar'),

    # Admin Gallery: Direct View
    path('admin/direct/<path:direct>', map_saver.views.MapGalleryView.as_view(), name='direct'),

    # Admin Gallery: Diff
    path('admin/diff/<slug:urlhash_first>/<slug:urlhash_second>/', map_saver.views.MapDiffView.as_view(), name='diff'),

    # Admin: Maps created by date
    path('admin/bydate/', map_saver.views.MapsByDateView.as_view(), name='by_date'),

    # Admin: Activity Log
    re_path(r'admin/activity/(?P<map>[\w\d\-\_]{8})/?$', never_cache(moderate.views.ActivityLogList.as_view()), name='activity_map'),
    re_path(r'admin/activity/(?P<user_id>\d+)?/?$', never_cache(moderate.views.ActivityLogList.as_view()), name='activity'),

    # Thumbnails
    path('admin/thumbnail/<slug:tag>/', map_saver.views.ThumbnailGalleryView.as_view(), name='thumbnail_tag'),

    # Admin and Moderation
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view()),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + \
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
