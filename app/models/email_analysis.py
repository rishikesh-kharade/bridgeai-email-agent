from sqlalchemy import String, Column, Integer, ForeignKey, Text, Boolean, DateTime, func, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base

class EmailAnalysis(Base):
    __tablename__ = "email_analysis"
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer , ForeignKey("emails.id"), nullable=False)
    email = relationship("Email", back_populates="analyses")
    summary = Column(Text, nullable = False)
    category = Column(String, nullable = False)
    priority = Column(String, nullable = False, default='normal')
    sentiment = Column(String, nullable = False, default='neutral')
    requires_action = Column(Boolean, nullable=False, default=False)
    requires_attention = Column(Boolean, nullable=False, default=False)
    action_items = Column(JSON, nullable=False, default=list)
    model_names = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())




