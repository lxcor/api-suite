from django.urls import include, path

urlpatterns = [
    path('', include('romma.urls')),
    path('reggi/', include('reggi.urls')),
]
