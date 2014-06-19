from __future__ import absolute_import

import os
from datetime import timedelta
from celery import Celery
from kombu import Exchange, Queue

"""
Convention is to use fabric env.project; if changed, change supervisor settings also.
"""

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
project = os.environ.get('DJANGO_SETTINGS_MODULE').split('.')[0]

app = Celery(project)
app.config_from_object('{0}.celeryconfig'.format(project))
app.conf.update(
    CELERY_IMPORTS = ("{0}.tasks".format(project),),
    NAME = project,
    CELERY_DEFAULT_QUEUE = project,
    CELERY_DEFAULT_EXCHANGE = project,
    CELERY_DEFAULT_ROUTING_KEY = project,
    CELERY_QUEUES = (
        Queue(project, Exchange(project), routing_key=project),
    ),
)

if os.environ.get('DJANGO_SETTINGS_MODULE') in ['settings.local']:
    app.conf.update(
        CELERY_ALWAYS_EAGER = True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS = True,
    )
