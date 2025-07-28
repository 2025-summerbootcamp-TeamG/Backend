"""
WSGI config for ticket_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

# OpenTelemetry 초기화 추가
from . import otel_init
otel_init.init_tracing()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_backend.settings')

application = get_wsgi_application()
