# celery.py

from __future__ import absolute_import, unicode_literals

import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet.settings")

app = Celery("wallet")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    "queue_transactions": {
        "task": "wallet.queue_transactions",
        "schedule": timedelta(seconds=30),
    }
}
