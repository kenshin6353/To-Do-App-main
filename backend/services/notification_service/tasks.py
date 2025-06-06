"""
Notification service async tasks - Real broker integration examples
"""
from utils.broker import app
from utils.db import SessionLocal
from .models import Notification
from services.user_service.models import User
from services.task_service.models import Task
from .logic import get_due_soon, get_overdue
from .mailer import send_email
from datetime import datetime, timedelta

@app.task(name='tasks.notification.send_instant_notification')
def send_instant_notification(user_id, title, message, notification_type="info"):
    """Send instant notification to user (triggered by user actions)"""
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        print(f"🔔 Sending instant notification to {user.email}: {title}")
        
        # Send email notification
        send_email(user.email, title, message)
        
        # Store notification in database
        notification = Notification(
            user_id=user_id,
            task_id=None,  # Not task-specific
            notify_type=notification_type,
            title=title,
            message=message,
            sent_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()
        
        return {
            "status": "success",
            "user_id": user_id,
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

@app.task(name='tasks.notification.send_task_completion_notification')
def send_task_completion_notification(task_id):
    """Send notification when a task is completed"""
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}
        
        user = db.query(User).get(task.user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        print(f"🎉 Sending task completion notification for '{task.title}'")
        
        # Send congratulatory email
        subject = f"Task Completed: {task.title}"
        message = f"""
        Congratulations! You've completed the task: "{task.title}"
        
        Keep up the great work! 🎉
        
        Your TodoApp Team
        """
        
        send_email(user.email, subject, message)
        
        # Store notification
        notification = Notification(
            user_id=user.id,
            task_id=task.id,
            notify_type="task_completed",
            title=subject,
            message=message,
            sent_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()
        
        return {
            "status": "success",
            "task_id": task_id,
            "user_email": user.email
        }
    finally:
        db.close()

@app.task(name='tasks.notification.send_daily_digest')
def send_daily_digest(user_id):
    """Send daily digest of tasks to user"""
    db = SessionLocal()
    try:
        user = db.query(User).get(user_id)
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Get user's tasks for digest
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        
        due_today = db.query(Task).filter(
            Task.user_id == user_id,
            Task.due_date >= today,
            Task.due_date < tomorrow,
            Task.completed == False
        ).all()
        
        overdue = db.query(Task).filter(
            Task.user_id == user_id,
            Task.due_date < today,
            Task.completed == False
        ).all()
        
        print(f"📅 Sending daily digest to {user.email}")
        
        # Create digest email
        subject = f"Daily Task Digest - {today.strftime('%B %d, %Y')}"
        
        message = f"""
        Good morning {user.username}!
        
        Here's your daily task summary:
        
        📋 Due Today ({len(due_today)} tasks):
        {chr(10).join([f"• {task.title}" for task in due_today]) if due_today else "No tasks due today! 🎉"}
        
        ⚠️ Overdue ({len(overdue)} tasks):
        {chr(10).join([f"• {task.title}" for task in overdue]) if overdue else "No overdue tasks! ✅"}
        
        Have a productive day!
        Your TodoApp Team
        """
        
        send_email(user.email, subject, message)
        
        return {
            "status": "success",
            "user_id": user_id,
            "due_today": len(due_today),
            "overdue": len(overdue)
        }
    finally:
        db.close()

@app.task(name='tasks.notification.process_bulk_notifications')
def process_bulk_notifications(notification_batch):
    """Process a batch of notifications efficiently"""
    db = SessionLocal()
    try:
        processed = 0
        failed = 0
        
        for notification_data in notification_batch:
            try:
                user_id = notification_data["user_id"]
                title = notification_data["title"]
                message = notification_data["message"]
                notify_type = notification_data.get("type", "bulk")
                
                user = db.query(User).get(user_id)
                if not user:
                    failed += 1
                    continue
                
                # Send notification
                send_email(user.email, title, message)
                
                # Store in database
                notification = Notification(
                    user_id=user_id,
                    task_id=notification_data.get("task_id"),
                    notify_type=notify_type,
                    title=title,
                    message=message,
                    sent_at=datetime.utcnow()
                )
                db.add(notification)
                processed += 1
                
            except Exception as e:
                print(f"❌ Failed to process notification: {e}")
                failed += 1
        
        db.commit()
        
        print(f"📬 Bulk notification processing complete: {processed} sent, {failed} failed")
        
        return {
            "status": "success",
            "processed": processed,
            "failed": failed,
            "total": len(notification_batch)
        }
    finally:
        db.close()

# Keep the original scheduled tasks but rename them for clarity
@app.task(name='tasks.notification.scheduled_due_soon_check')
def scheduled_due_soon_check():
    """Scheduled task to check for due soon tasks (runs via Celery Beat)"""
    db = SessionLocal()
    try:
        notifications_sent = 0
        for task in get_due_soon(db):
            # Skip if already sent
            if db.query(Notification).filter_by(task_id=task.id, notify_type="due_soon").first():
                continue
            
            user = db.query(User).get(task.user_id)
            if not user:
                continue
            
            send_email(
                user.email,
                f"Reminder: '{task.title}' due soon",
                f"Your task '{task.title}' is due at {task.due_date.isoformat()} UTC."
            )
            
            db.add(Notification(task_id=task.id, user_id=user.id, notify_type="due_soon"))
            notifications_sent += 1
        
        db.commit()
        print(f"⏰ Scheduled check complete: {notifications_sent} due-soon notifications sent")
        
        return {"status": "success", "notifications_sent": notifications_sent}
    finally:
        db.close()

@app.task(name='tasks.notification.scheduled_overdue_check')
def scheduled_overdue_check():
    """Scheduled task to check for overdue tasks (runs via Celery Beat)"""
    db = SessionLocal()
    try:
        notifications_sent = 0
        for task in get_overdue(db):
            if db.query(Notification).filter_by(task_id=task.id, notify_type="overdue").first():
                continue
            
            user = db.query(User).get(task.user_id)
            if not user:
                continue
            
            send_email(
                user.email,
                f"Overdue: '{task.title}'",
                f"Your task '{task.title}' was due at {task.due_date.isoformat()} UTC and is now overdue."
            )
            
            db.add(Notification(task_id=task.id, user_id=user.id, notify_type="overdue"))
            notifications_sent += 1
        
        db.commit()
        print(f"⚠️ Scheduled check complete: {notifications_sent} overdue notifications sent")
        
        return {"status": "success", "notifications_sent": notifications_sent}
    finally:
        db.close() 