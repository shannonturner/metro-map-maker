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

from map_saver.views import MapDataView, MapDiffView, MapGalleryView, MapAdminActionView, MapSimilarView, MapsByDateView, ThumbnailGalleryView, HomeView, PublicGalleryView, CreatorNameMapView
from moderate.views import ActivityLogList

urlpatterns = [
    # Main page
    path('', HomeView.as_view(), name='home'),

    # Public Gallery
    path('gallery/', PublicGalleryView.as_view(), name='public_gallery'),

    # End-user actions (saving, loading, naming maps)
    path('save/', MapDataView.as_view(), name='save_map'),
    path('load/<slug:urlhash>', MapDataView.as_view(), name='load_map'),
    path('name/', CreatorNameMapView.as_view(), name='name_map'),

    # Admin and Moderation
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view()),

    # Admin Gallery
    re_path(r'admin/gallery/(?P<tag>[\w^\d]+)?/?$', MapGalleryView.as_view(), name='admin_gallery'),

    # Admin Gallery: Admin actions
    path('admin/action/', MapAdminActionView.as_view(), name='admin_action'),

    # Admin Gallery: Similar
    path('admin/similar/<slug:urlhash>', MapSimilarView.as_view(), name='similar'),

    # Admin Gallery: Direct View
    path('admin/direct/<path:direct>', MapGalleryView.as_view(), name='direct'),

    # Admin Gallery: Diff
    path('admin/diff/<slug:urlhash_first>/<slug:urlhash_second>/', MapDiffView.as_view(), name='diff'),

    # Admin: Maps created by date
    path('admin/bydate/', MapsByDateView.as_view(), name='by_date'),

    # Admin: Activity Log
    re_path(r'admin/activity/(?P<map>[\w\d\-\_]{8})/?$', ActivityLogList.as_view(), name='activity_map'),
    re_path(r'admin/activity/(?P<user_id>\d+)?/?$', ActivityLogList.as_view(), name='activity'),

    # Thumbnails
    path('admin/thumbnail/<slug:tag>/', ThumbnailGalleryView.as_view(), name='thumbnail_tag'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
