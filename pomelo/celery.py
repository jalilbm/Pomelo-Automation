from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from kombu import Exchange, Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pomelo.settings")

app = Celery("pomelo")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

CELERY_QUEUES = (
    Queue(
        "handle_messages_activation_queue", Exchange("default"), routing_key="default"
    ),
    # ... any other queues you might have
)
