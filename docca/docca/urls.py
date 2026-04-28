"""URL configuration for the docca documentation portal."""

from django.urls import path

from docca.views import EndpointDetailView, ManifestView, PortalView

urlpatterns = [
    path('', PortalView.as_view(), name='docca.portal'),
    path('endpoint/<slug:slug>/', EndpointDetailView.as_view(), name='docca.endpoint_detail'),
    path('manifest.json', ManifestView.as_view(), name='docca.manifest'),
]
