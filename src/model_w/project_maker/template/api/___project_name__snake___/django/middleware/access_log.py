"""
Middleware for access logs.
We don't use standard Granian logging, as we can't get the real IP address, as
request headers aren't part of the atoms for Granian log configuration.

Access logs are written straight to stdout rather than through the logging
module: otherwise they would end up in Sentry (as breadcrumbs or events),
which is noise we don't want.
"""

import logging
import sys
import time
from typing import TYPE_CHECKING

from ipware import get_client_ip

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

# Silence the django.server logger
logging.getLogger("django.server").setLevel(logging.CRITICAL)


class RequestLogMiddleware:
    """Request Logging Middleware."""

    def __init__(self, get_response):
        """Initialise the middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        """Call the middleware and log the request."""
        start_time = time.time()
        request_method = request.method
        request_path = request.build_absolute_uri()
        user_agent = request.headers.get("User-Agent")
        client_ip = self.get_real_ip(request)

        response: HttpResponse = self.get_response(request)

        run_time = time.time() - start_time

        msg = (
            f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] "
            f'{client_ip} "{request_method} - {request_path}" '
            f'{response.status_code} ({int(run_time * 1000)}ms) "{user_agent}"'
        )

        sys.stdout.write(f"{msg}\n")
        sys.stdout.flush()

        return response

    def get_real_ip(self, request: HttpRequest) -> str:
        """
        Try and get the real IP address of the client.
        If we can't get it, return an empty string.
        """
        client_ip, _is_routable = get_client_ip(request)
        return client_ip if client_ip else ""
