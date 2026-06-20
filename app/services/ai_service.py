import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logger import logger

class AIService:
    def __init__(self):
        if settings.AI_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL
            )
        else:
            self.client = None
            
    async def analyze_comment(self, comment: str) -> dict:
        """
        Анализирует комментарий и генерирует авто-ответ.
        Возвращает словарь: {"sentiment": "...", "reply": "..."}
        """
        
        fallback_data = {
            "sentiment": "neutral",
            "reply": "Спасибо за ваше обращение! Я свяжусь с вами в ближайшее время."
        }
        
        if not self.client:
            logger.warning("AI Service: API key is missing. Using fallback response.")
            return fallback_data
        
        system_prompt = (
            "You are an AI assistant built into a web developer's portfolio website.\n"
            "Analyze the user's comment and return a JSON object with exactly two keys:\n"
            "1. 'sentiment': string, strictly one of ['positive', 'neutral', 'negative']\n"
            "2. 'reply': string, a polite and professional automated reply in Russian "
            "addressing the user's comment.\n"
            "Output ONLY valid JSON. No markdown formatting, no code blocks."
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User comment: {comment}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                timeout=5.0
            )
            
            ai_text = response.choices[0].message.content
            result = json.loads(ai_text)
            
            if "sentiment" in result and "reply" in result:
                return result

            return fallback_data
        except Exception as e:
            logger.error(f"AI Service Error: {str(e)}. Graceful fallback applied.", exc_info=True)
            return fallback_data