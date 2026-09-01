from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.db.database import Base

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    tasks = relationship("Task", back_populates="email")
    analyses = relationship("EmailAnalysis", back_populates="email")
    provider_message_id = Column(String, unique=True, index=True, nullable=False)
    sender = Column(String, nullable=False)
    receiver = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    processing_status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
