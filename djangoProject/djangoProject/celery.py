# myproject/celery.py
import os
from djangoProject.celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
app = Celery('djangoProject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()