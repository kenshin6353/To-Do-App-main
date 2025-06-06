"""
Updated worker using shared broker - demonstrates real distributed processing
"""
from utils.broker import app  # Use shared Celery app
from datetime import datetime
from utils.db import engine, Base, SessionLocal

# Configure Celery Beat schedule for the shared app
app.conf.beat_schedule = {
    "due-soon-every-30-seconds": {
        "task": "tasks.notification.scheduled_due_soon_check",
        "schedule": 30.0  # Every 30 seconds for demo
    },
    "overdue-every-30-seconds": {
        "task": "tasks.notification.scheduled_overdue_check", 
        "schedule": 30.0  # Every 30 seconds for demo
    },
    "daily-digest-at-9am": {
        "task": "tasks.notification.send_daily_digest",
        "schedule": 60.0,  # For demo, run every minute
        "args": [1]  # Send to user ID 1 for demo
    },
}

# Ensure notifications table exists
Base.metadata.create_all(bind=engine)

# Import all task modules to register them with the shared broker
try:
    from services.notification_service.tasks import *
    from services.user_service.tasks import *
    from services.task_service.tasks import *
    print("✅ All task modules loaded successfully - broker integration active!")
except ImportError as e:
    print(f"⚠️ Warning: Could not import task modules: {e}")

# The actual task implementations are now in the tasks.py files
# This worker.py file now just configures the shared Celery app and schedules
