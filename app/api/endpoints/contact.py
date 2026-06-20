from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.schemas.contact import ContactCreate
from app.services.contact_service import ContactService
from app.middlewares.rate_limiter import rate_limiter

router = APIRouter(prefix="/contact", tags=["Contact Form"])

contact_service = ContactService()

@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter)])
async def submit_contact_form(
    payload: ContactCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        result = await contact_service.process_contact_form(
            db=db, payload=payload, background_tasks=background_tasks
        )
        
        return {
            "success": True,
            "message": "Обращение принято, уведомления отправлены.",
            "data": {
                "id": result.id,
                "name": result.name
            },
            "ai_reply": result.ai_reply
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки формы: {str(e)}"
        )