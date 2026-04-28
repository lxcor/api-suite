"""Minimal URL configuration used by docca tests."""

from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView


class AlphaView(APIView):
    """List alpha resources."""

    docca_tag = 'Alpha'
    docca_overview = 'Alpha overview text.'

    def get(self, request):
        return Response([])

    def post(self, request):
        return Response({}, status=201)


class BetaView(APIView):
    """Retrieve a beta resource."""

    docca_tag = 'Beta'

    def get(self, request, pk):
        return Response({})


urlpatterns = [
    path('api/alpha/', AlphaView.as_view(), name='alpha.list'),
    path('api/beta/<int:pk>/', BetaView.as_view(), name='beta.detail'),
    path('docs/', include('docca.urls')),
]
