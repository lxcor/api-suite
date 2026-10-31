from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from .sitemaps import SuiteSitemap

# Admin branding follows the site name (REGGI_SITE_NAME, default "API-Suite").
admin.site.site_header = settings.REGGI_SITE_NAME
admin.site.site_title = settings.REGGI_SITE_NAME
admin.site.index_title = 'Administration'

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': {'pages': SuiteSitemap}}, name='sitemap'),
    path('admin/', admin.site.urls),
    path('reggi/', include('reggi.urls')),
    path('usage/', include('kotta.urls')),
    path('docs/', include('docca.urls')),
    path('', include('billa.urls')),
    path('', include('romma.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
