from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('reggi.urls')),
    path('usage/', include('kotta.urls')),
    path('docs/', include('docca.urls')),
    path('', include('billa.urls')),
    path('', include('romma.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
