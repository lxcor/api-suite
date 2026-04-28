"""Middleware for kotta — extracts and attaches the client IP address to each request."""

from django.conf import settings


def _get_client_ip(request):
    """Extract the client IP address from the request.

    When ``KOTTA_TRUST_PROXY_HEADERS`` is ``True`` in settings, the
    ``X-Forwarded-For`` header is read first so that requests arriving
    via a reverse proxy (nginx, load balancer) are identified by the
    originating client IP rather than the proxy IP.  The first address
    in the header chain is used as it represents the original client.

    Falls back to ``REMOTE_ADDR`` when the header is absent or proxy
    trust is disabled.

    Parameters
    ----------
    request : HttpRequest
        The incoming HTTP request.

    Returns
    -------
    str
        The resolved client IP address string.
    """
    trust_proxy = getattr(settings, 'KOTTA_TRUST_PROXY_HEADERS', False)

    if trust_proxy:
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR', '')


class KottaMiddleware:
    """Attach the resolved client IP address to the request as ``request.kotta_ip``.

    Must be placed after ``django.contrib.auth.middleware.AuthenticationMiddleware``
    in ``MIDDLEWARE`` so that ``request.user`` is available to the throttle
    classes that run downstream.
    """

    def __init__(self, get_response):
        """Store the next middleware or view in the chain."""
        self.get_response = get_response

    def __call__(self, request):
        """Resolve and attach the client IP then pass the request down the chain."""
        request.kotta_ip = _get_client_ip(request)
        return self.get_response(request)
