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

from django.urls import include, path
from django.contrib import admin
from django.conf import settings

from map_saver.views import MapDataView, MapDiffView, MapGalleryView, MapAdminActionView, MapSimilarView, MapsByDateView, ThumbnailGalleryView, HomeView, PublicGalleryView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('gallery/', PublicGalleryView.as_view(), name='public_gallery'),
    path('admin/gallery/<int:page>', MapGalleryView.as_view(), name='gallery'),
    path('admin/gallery/<slug:tag>/<int:page>', MapGalleryView.as_view(), name='gallery'),
    path('admin/gallery/<slug:tag>', MapGalleryView.as_view(), name='gallery'),
    path('admin/direct/<path:direct>', MapGalleryView.as_view(), name='direct'),
    path('admin/thumbnail/<slug:tag>/<int:page>', ThumbnailGalleryView.as_view(), name='thumbnail'),
    path('admin/thumbnail/<slug:tag>', ThumbnailGalleryView.as_view(), name='thumbnail'),
    path('admin/similar/<slug:urlhash>', MapSimilarView.as_view(), name='similar'),
    path('admin/diff/<slug:urlhash_first>/<slug:urlhash_second>', MapDiffView.as_view(), name='diff'),
    path('admin/action/', MapAdminActionView.as_view(), name='admin_action'),
    path('save/', MapDataView.as_view(), name='save_map'),
    path('load/<slug:urlhash>', MapDataView.as_view(), name='load_map'),
    path('admin/bydate/', MapsByDateView.as_view(), name='by_date'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
