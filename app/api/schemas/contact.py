from pydantic import BaseModel, EmailStr, Field

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Имя пользователя")
    phone: str = Field(..., min_length=5, max_length=20, description="Номер телефона")
    
    email: EmailStr = Field(..., description="Электронная почта для связи")
    comment: str = Field(..., min_length=10, max_length=1000, description="Текст обращения")