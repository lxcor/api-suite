"""URL configuration for the kotta usage dashboard."""

from django.urls import path

from kotta.views import usage

urlpatterns = [
    path('', usage, name='kotta.usage'),
]
