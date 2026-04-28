from django.urls import include, path

urlpatterns = [
    path('', include('billa.urls')),
    path('reggi/', include('reggi.urls')),
]
