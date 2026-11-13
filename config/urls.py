"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from importlib.util import find_spec

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.news.sitemaps import (
    ArticleSitemap,
    DriverSitemap,
    StaticViewSitemap,
    TeamSitemap,
)

sitemaps = {
    'articles': ArticleSitemap,
    'static': StaticViewSitemap,
    'drivers': DriverSitemap,
    'teams': TeamSitemap,
}

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('apps.news.urls')),
    path('calendar/', include('apps.grandprix_calendar.urls')),
    path('racing/', include('apps.racing.urls')),
    path('summernote/', include('django_summernote.urls')),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS and find_spec("debug_toolbar") is not None:
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
