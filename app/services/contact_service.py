from sqlalchemy.orm import Session
from app.api.schemas.contact import ContactCreate
from app.repositories import contact_repository
from app.services.email_service import EmailService
from app.services.ai_service import AIService

class ContactService:
    def __init__(self):
        self.email_service = EmailService()
        self.ai_service = AIService()

    async def process_contact_form(self, db: Session, payload: ContactCreate):
        ai_analytics = await self.ai_service.analyze_comment(payload.comment)
        
        message_data = payload

        new_message = contact_repository.create_contact_message_with_ai(
            db=db, 
            message_data=payload,
            sentiment=ai_analytics["sentiment"],
            reply=ai_analytics["reply"]
        )
        
        await self.email_service.send_contact_emails(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            comment=f"{payload.comment}\n\n[AI Анализ тональности: {ai_analytics['sentiment']}]",
            ai_reply=ai_analytics["reply"]
        )
        
        return new_message