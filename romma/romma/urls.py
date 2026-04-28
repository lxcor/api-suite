from django.urls import path

from romma.views import endpoints, home, robots_txt

urlpatterns = [
    path('', home, name='romma.index'),
    path('endpoints/', endpoints, name='romma.endpoints'),
    path('robots.txt', robots_txt, name='romma.robots_txt'),
]
