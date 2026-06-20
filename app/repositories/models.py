from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    comment = Column(Text, nullable=False)
    
    ai_sentiment = Column(String, nullable=True)  # Тональность (positive/neutral/negative)
    ai_reply = Column(Text, nullable=True)      # Сгенерированный ИИ ответ
    
    created_at = Column(DateTime, default=datetime.utcnow)