"""
Middleware for access logs.
We don't use standard Granian logging, as we can't get the real IP address, as
request headers aren't part of the atoms for Granian log configuration.
"""

import logging
import time

import coloredlogs
from django.http import HttpRequest, HttpResponse
from ipware import get_client_ip

logger = logging.getLogger(__name__)

logger.propagate = False
handler = logging.StreamHandler()
formatter = coloredlogs.ColoredFormatter("%(message)s")
handler.setFormatter(formatter)
logger.handlers = [handler]

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

        if response.status_code < 400:
            logger.info(msg=msg)
        elif response.status_code < 500:
            logger.warning(msg=msg)
        else:
            logger.error(msg=msg)

        return response

    def get_real_ip(self, request: HttpRequest) -> str:
        """
        Try and get the real IP address of the client.
        If we can't get it, return an empty string.
        """
        client_ip, _is_routable = get_client_ip(request)
        return client_ip if client_ip else ""
