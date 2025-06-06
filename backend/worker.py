#!/usr/bin/env python3
"""
Celery worker script that imports all tasks and starts the worker
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/app/backend')

# Import the Celery app
from utils.broker import app

# Import all task modules to register them with Celery
try:
    from services.user_service.tasks import *
    print("✅ User service tasks imported successfully")
except ImportError as e:
    print(f"⚠️  Could not import user service tasks: {e}")

try:
    from services.task_service.tasks import *
    print("✅ Task service tasks imported successfully")
except ImportError as e:
    print(f"⚠️  Could not import task service tasks: {e}")

try:
    from services.notification_service.tasks import *
    print("✅ Notification service tasks imported successfully")
except ImportError as e:
    print(f"⚠️  Could not import notification service tasks: {e}")

if __name__ == '__main__':
    # Start the worker
    app.start() 