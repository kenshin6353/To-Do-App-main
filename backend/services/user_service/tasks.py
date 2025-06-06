"""
User service async tasks - Real broker integration examples
"""
from utils.broker import app
from utils.db import SessionLocal
from .models import User
from services.task_service.models import Task
from datetime import datetime, timedelta
import requests
import os

@app.task(name='tasks.user.send_welcome_email')
def send_welcome_email(user_id):
    """Send welcome email when user registers"""
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Simulate email sending (replace with real email service)
        print(f"📧 Sending welcome email to {user.email}")
        
        # In real app, you'd use SendGrid, SES, etc.
        # send_email_via_service(user.email, "Welcome!", welcome_template)
        
        return {"status": "success", "email": user.email}
    finally:
        db.close()

@app.task(name='tasks.user.create_default_tasks')
def create_default_tasks(user_id):
    """Create default tasks for new users"""
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Create helpful default tasks
        default_tasks = [
            {
                "title": "Welcome to TodoApp! 👋",
                "description": "Complete this task to get started",
                "due_date": datetime.utcnow() + timedelta(days=1)
            },
            {
                "title": "Explore the features",
                "description": "Try creating, editing, and completing tasks",
                "due_date": datetime.utcnow() + timedelta(days=3)
            },
            {
                "title": "Set up your profile",
                "description": "Add your preferences and settings",
                "due_date": datetime.utcnow() + timedelta(days=7)
            }
        ]
        
        created_tasks = []
        for task_data in default_tasks:
            task = Task(
                user_id=user_id,
                title=task_data["title"],
                description=task_data["description"],
                due_date=task_data["due_date"],
                completed=False
            )
            db.add(task)
            created_tasks.append(task_data["title"])
        
        db.commit()
        print(f"✅ Created {len(created_tasks)} default tasks for user {user.username}")
        
        return {"status": "success", "tasks_created": len(created_tasks)}
    finally:
        db.close()

@app.task(name='tasks.user.update_user_stats')
def update_user_stats(user_id):
    """Update user statistics (task completion rate, etc.)"""
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Calculate user stats
        total_tasks = db.query(Task).filter_by(user_id=user_id).count()
        completed_tasks = db.query(Task).filter_by(user_id=user_id, completed=True).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        print(f"📊 User {user.username} stats: {completed_tasks}/{total_tasks} tasks completed ({completion_rate:.1f}%)")
        
        # In a real app, you'd store these stats in a user_stats table
        # or send to analytics service
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate
        }
    finally:
        db.close()

@app.task(name='tasks.user.sync_to_external_service')
def sync_to_external_service(user_id, action, data):
    """Sync user data to external services (CRM, analytics, etc.)"""
    try:
        # Simulate external API call
        print(f"🔄 Syncing user {user_id} action '{action}' to external services")
        
        # Example: Send to analytics service
        analytics_payload = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # In real app, you'd call external APIs:
        # requests.post("https://analytics.example.com/events", json=analytics_payload)
        # requests.post("https://crm.example.com/user-activity", json=analytics_payload)
        
        print(f"📈 Analytics event sent: {action}")
        
        return {"status": "success", "action": action, "synced_services": ["analytics", "crm"]}
    except Exception as e:
        print(f"❌ Failed to sync to external service: {e}")
        return {"status": "error", "message": str(e)} 