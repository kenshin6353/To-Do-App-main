"""
Shared broker utilities for distributed task processing
"""
from celery import Celery
from .config import BROKER_URL

# Shared Celery app instance
app = Celery("todoapp_distributed", broker=BROKER_URL)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_routes={
        'tasks.user.*': {'queue': 'user_queue'},
        'tasks.task.*': {'queue': 'task_queue'},
        'tasks.notification.*': {'queue': 'notification_queue'},
        'tasks.analytics.*': {'queue': 'analytics_queue'},
    }
)

# Tasks will be imported manually by the worker process
# This avoids module discovery issues during startup 