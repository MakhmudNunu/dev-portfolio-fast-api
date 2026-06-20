from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime 

from app.database import get_db
from app.repositories import models

router = APIRouter(prefix="", tags=["System Metrics"])

@router.get("/health")
async def health_check():
    """Проверка статуса работоспособности сервиса"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Выгрузка статистики обращений из базы данных"""
    total_messages = db.query(models.ContactMessage).count()
    
    sentiment_stats = db.query(
        models.ContactMessage.ai_sentiment, 
        func.count(models.ContactMessage.id)
    ).group_by(models.ContactMessage.ai_sentiment).all()
    
    breakdown = {sentiment or "unknown": count for sentiment, count in sentiment_stats}

    return {
        "total_submissions": total_messages,
        "ai_sentiment_breakdown": breakdown
    }