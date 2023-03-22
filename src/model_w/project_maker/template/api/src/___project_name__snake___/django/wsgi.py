"""
WSGI config for ___project_name__snake___ project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "___project_name__snake___.django.settings")

application = get_wsgi_application()
