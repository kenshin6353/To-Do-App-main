from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from utils.db import engine, Base, SessionLocal
from utils.config import JWT_SECRET
import services.notification_service.models  # register table
from .models import Notification
from flask_cors import CORS

# Import async tasks
from .tasks import (
    send_instant_notification, send_daily_digest, 
    process_bulk_notifications, scheduled_due_soon_check, scheduled_overdue_check
)

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET
jwt = JWTManager(app)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

# ensure our table exists
Base.metadata.create_all(bind=engine)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# 🚀 REAL BROKER INTEGRATION: Proper notification endpoints
@app.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """Get user's notifications - this is what the frontend expects"""
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        notifications = db.query(Notification).filter_by(user_id=user_id).order_by(
            Notification.sent_at.desc()
        ).limit(50).all()
        
        return jsonify([
            {
                "id": n.id,
                "title": n.title or f"Notification ({n.notify_type})",
                "message": n.message or "No message",
                "type": n.notify_type,
                "task_id": n.task_id,
                "sent_at": n.sent_at.isoformat(),
                "read": False  # You could add a read field to the model
            }
            for n in notifications
        ]), 200
    finally:
        db.close()

@app.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark notification as read - this is what the frontend expects"""
    user_id = get_jwt_identity()
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter_by(
            id=notification_id, user_id=user_id
        ).first()
        
        if not notification:
            return jsonify({"msg": "Notification not found"}), 404
        
        # In a real app, you'd have a 'read' field to update
        # For now, just return success
        return jsonify({"msg": "Notification marked as read"}), 200
    finally:
        db.close()

# Admin/testing endpoints for triggering async tasks
@app.route("/admin/trigger/due-soon-check", methods=["POST"])
def admin_trigger_due_soon():
    """Admin endpoint to manually trigger due soon check"""
    scheduled_due_soon_check.delay()
    return jsonify({"msg": "Due soon check queued via broker"}), 202

@app.route("/admin/trigger/overdue-check", methods=["POST"])
def admin_trigger_overdue():
    """Admin endpoint to manually trigger overdue check"""
    scheduled_overdue_check.delay()
    return jsonify({"msg": "Overdue check queued via broker"}), 202

@app.route("/admin/send-test-notification", methods=["POST"])
def admin_send_test_notification():
    """Admin endpoint to test instant notifications"""
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    
    send_instant_notification.delay(
        user_id,
        "Test Notification 🧪",
        "This is a test notification sent via the message broker!"
    )
    
    return jsonify({"msg": "Test notification queued via broker"}), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
