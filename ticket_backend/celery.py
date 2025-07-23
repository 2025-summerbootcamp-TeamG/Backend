import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_backend.settings')

app = Celery('ticket_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() 