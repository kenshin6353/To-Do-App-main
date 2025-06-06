from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from utils.db import Base

class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    task_id     = Column(Integer, nullable=True, index=True)  # Allow null for non-task notifications
    user_id     = Column(Integer, nullable=False, index=True)
    notify_type = Column(String, nullable=False)  # 'due_soon', 'overdue', 'task_completed', 'info', etc.
    title       = Column(String, nullable=True)   # Notification title
    message     = Column(Text, nullable=True)     # Notification message content
    sent_at     = Column(DateTime, default=datetime.utcnow)
