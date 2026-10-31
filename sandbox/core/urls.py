from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from romma.views import robots_txt
from django.contrib.sitemaps.views import sitemap
from .sitemaps import SuiteSitemap

# Admin branding follows the site name (REGGI_SITE_NAME, default "API-Suite").
admin.site.site_header = settings.REGGI_SITE_NAME
admin.site.site_title = settings.REGGI_SITE_NAME
admin.site.index_title = 'Administration'

urlpatterns = [
    # Thin sandbox homepage; romma's own homepage lives at /romma/.
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('robots.txt', robots_txt),
    path('endpoints/', RedirectView.as_view(pattern_name='romma.endpoints', permanent=True)),
    path('sitemap.xml', sitemap, {'sitemaps': {'pages': SuiteSitemap}}, name='sitemap'),
    path('admin/', admin.site.urls),
    path('reggi/', include('reggi.urls')),
    path('usage/', include('kotta.urls')),
    path('docs/', include('docca.urls')),
    path('', include('billa.urls')),
    path('romma/', include('romma.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
