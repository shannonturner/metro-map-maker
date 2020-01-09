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

import map_saver.views
import moderate.views

urlpatterns = [
    # Main page
    path('', map_saver.views.HomeView.as_view(), name='home'),

    # Public Gallery
    path('gallery/', map_saver.views.PublicGalleryView.as_view(), name='public_gallery'),

    # End-user actions (saving, loading, naming maps)
    path('save/', map_saver.views.MapDataView.as_view(), name='save_map'),
    path('load/<slug:urlhash>', map_saver.views.MapDataView.as_view(), name='load_map'),
    path('name/', map_saver.views.CreatorNameMapView.as_view(), name='name_map'),

    # Admin and Moderation
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view()),

    # Admin HQ
    path('admin/home/', map_saver.views.AdminHomeView.as_view(), name='admin_home'),

    # Admin Gallery
    re_path(r'admin/gallery/(?P<tag>[\w\-\_^\d]+)?/?$', map_saver.views.MapGalleryView.as_view(), name='admin_gallery'),

    # Admin Gallery: Admin actions
    path('admin/action/', map_saver.views.MapAdminActionView.as_view(), name='admin_action'),

    # Admin Gallery: Similar
    path('admin/similar/<slug:urlhash>', map_saver.views.MapSimilarView.as_view(), name='similar'),

    # Admin Gallery: Direct View
    path('admin/direct/<path:direct>', map_saver.views.MapGalleryView.as_view(), name='direct'),

    # Admin Gallery: Diff
    path('admin/diff/<slug:urlhash_first>/<slug:urlhash_second>/', map_saver.views.MapDiffView.as_view(), name='diff'),

    # Admin: Maps created by date
    path('admin/bydate/', map_saver.views.MapsByDateView.as_view(), name='by_date'),

    # Admin: Activity Log
    re_path(r'admin/activity/(?P<map>[\w\d\-\_]{8})/?$', moderate.views.ActivityLogList.as_view(), name='activity_map'),
    re_path(r'admin/activity/(?P<user_id>\d+)?/?$', moderate.views.ActivityLogList.as_view(), name='activity'),

    # Thumbnails
    path('admin/thumbnail/<slug:tag>/', map_saver.views.ThumbnailGalleryView.as_view(), name='thumbnail_tag'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
