from sqlalchemy.orm import Session
from app.repositories import models
from app.api.schemas import contact as schemas

def create_contact_message_with_ai(db: Session, message_data: schemas.ContactCreate, sentiment: str, reply: str):
    db_message = models.ContactMessage(
        name=message_data.name,
        phone=message_data.phone,
        email=message_data.email,
        comment=message_data.comment,
        ai_sentiment=sentiment,
        ai_reply=reply
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message