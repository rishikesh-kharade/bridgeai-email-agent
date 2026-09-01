from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=False )
    email = relationship("Email", back_populates="tasks")
    user = relationship("User", back_populates="tasks")
    assigned_to_id = Column(Integer, ForeignKey('users.id') , nullable = False)
    title = Column(String, nullable = False)
    description = Column(Text, nullable = False)
    status = Column(String,nullable=False, default='pending')
    priority = Column(String, nullable = False, default='normal')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default= func.now(), onupdate=func.now())



