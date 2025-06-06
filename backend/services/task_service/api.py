# services/task_service/api.py

from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity
)
from sqlalchemy.exc import IntegrityError
from utils.config import JWT_SECRET      # from utils/config.py
from utils.db     import SessionLocal, engine, Base
from .models      import Task
from services.user_service.models import User
from flask_cors import CORS

# Import async tasks for real broker integration
from .tasks import (
    schedule_reminder, notify_team_members, update_project_progress,
    generate_task_analytics, backup_task_data
)
from services.notification_service.tasks import (
    send_instant_notification, send_task_completion_notification
)
from services.user_service.tasks import update_user_stats, sync_to_external_service

# ensure tables exist
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET
jwt = JWTManager(app)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


@app.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    data = request.get_json() or {}
    for f in ("title", "due_date"):
        if f not in data:
            return jsonify({"msg": f"'{f}' is required"}), 400

    try:
        due = datetime.fromisoformat(data["due_date"])
    except ValueError:
        return jsonify({"msg": "Invalid due_date. Use ISO format"}), 400

    user_id = get_jwt_identity()
    db = SessionLocal()
    task = Task(
        user_id=user_id,
        title=data["title"],
        description=data.get("description", ""),
        due_date=due
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 🚀 REAL BROKER INTEGRATION: Trigger async tasks after task creation
    print(f"🎯 Task {task.id} created - triggering async tasks via broker")
    
    # Schedule reminder if task is due soon
    if due <= datetime.utcnow() + timedelta(days=2):
        reminder_time = due - timedelta(hours=2)  # Remind 2 hours before
        schedule_reminder.delay(task.id, reminder_time.isoformat())
    
    # Check if this is a high-priority task (you could add priority field)
    priority = data.get("priority", "normal")
    if priority == "high":
        notify_team_members.delay(task.id)
    
    # Backup task data to external storage
    backup_task_data.delay(task.id)
    
    # Update user statistics
    update_user_stats.delay(user_id)
    
    # Send analytics event
    sync_to_external_service.delay(user_id, "task_created", {
        "task_id": task.id,
        "title": task.title,
        "due_date": task.due_date.isoformat(),
        "priority": priority
    })
    
    # Send instant notification to user
    send_instant_notification.delay(
        user_id,
        "Task Created Successfully! 📝",
        f"Your task '{task.title}' has been created and is due on {due.strftime('%B %d, %Y')}."
    )
    
    db.close()

    return (
        jsonify({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date.isoformat(),
            "completed": task.completed,
            "msg": "Task created! Background processing initiated."
        }),
        201
    )


@app.route("/tasks", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    db = SessionLocal()
    tasks = db.query(Task).filter_by(user_id=user_id).all()
    db.close()
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": t.due_date.isoformat(),
            "completed": t.completed
        }
        for t in tasks
    ]), 200


@app.route("/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    db = SessionLocal()
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    db.close()
    if not task:
        return jsonify({"msg": "Not found"}), 404
    return jsonify({
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat(),
        "completed": task.completed
    }), 200


@app.route("/tasks/<int:task_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_task(task_id):
    data = request.get_json() or {}
    user_id = get_jwt_identity()
    db = SessionLocal()
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if not task:
        db.close()
        return jsonify({"msg": "Not found"}), 404

    # Track if task was completed in this update
    was_completed = task.completed
    task_completion_triggered = False

    # apply updates if present
    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "due_date" in data:
        try:
            task.due_date = datetime.fromisoformat(data["due_date"])
        except ValueError:
            db.close()
            return jsonify({"msg": "Invalid due_date"}), 400
    if "completed" in data:
        task.completed = bool(data["completed"])
        # Check if task was just completed
        if not was_completed and task.completed:
            task_completion_triggered = True

    db.commit()
    db.refresh(task)
    
    # 🚀 REAL BROKER INTEGRATION: Trigger async tasks after task update
    if task_completion_triggered:
        print(f"🎯 Task {task.id} completed - triggering async tasks via broker")
        
        # Send task completion notification
        send_task_completion_notification.delay(task.id)
        
        # Update project progress
        update_project_progress.delay(task.id)
        
        # Update user statistics
        update_user_stats.delay(user_id)
        
        # Generate analytics for task completion patterns
        generate_task_analytics.delay(user_id)
        
        # Sync completion event to external services
        sync_to_external_service.delay(user_id, "task_completed", {
            "task_id": task.id,
            "title": task.title,
            "completion_time": datetime.utcnow().isoformat()
        })
    
    # Always backup updated task data
    backup_task_data.delay(task.id)
    
    db.close()
    
    response_data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat(),
        "completed": task.completed
    }
    
    if task_completion_triggered:
        response_data["msg"] = "Task completed! Congratulations notification and analytics are being processed."
    
    return jsonify(response_data), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    db = SessionLocal()
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if not task:
        db.close()
        return jsonify({"msg": "Not found"}), 404

    db.delete(task)
    db.commit()
    db.close()
    return jsonify({"msg": "Deleted"}), 200


if __name__ == "__main__":
    # pick a port that doesn’t collide with user-service
    app.run(host="0.0.0.0", port=5002, debug=True)
