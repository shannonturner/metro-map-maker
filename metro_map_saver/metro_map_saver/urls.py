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
from django.conf.urls import url
from django.contrib import admin

from map_saver.views import MapDataView, MapGalleryView

urlpatterns = [
    url(r'^(?:save/)?admin/', admin.site.urls),
    url(r'^(?:save/)?admin/gallery/(?P<page>[0-9]+)?$', MapGalleryView.as_view(), name='gallery'),
    url(r'^(?:save/)?$', MapDataView.as_view(), name='save_map'),
    url(r'^(?:save/)?(?P<urlhash>[0-9a-zA-Z\-\_]+)$', MapDataView.as_view(), name='load_map'),
]
