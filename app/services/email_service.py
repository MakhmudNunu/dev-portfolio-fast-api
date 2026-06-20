import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.logger import logger

# Определяем базовый путь к папке с шаблонами
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

class EmailService:
    @staticmethod
    def _send_sync_email(to_email: str, subject: str, html_content: str):
        """Внутренний синхронный метод отправки почты через SMTP"""
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
        
    def _load_template(self, filename: str) -> str:
        """Вспомогательный метод для чтения HTML файлов"""
        file_path = os.path.join(TEMPLATES_DIR, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    async def send_contact_emails(self, name: str, email: str, phone: str, comment: str, ai_reply: str = None):
        """Основной асинхронный метод для отправки двух писем"""
        
        # 1. Загружаем и форматируем шаблон для владельца
        owner_template = self._load_template("owner_email.html")
        owner_html = owner_template.format(name=name, email=email, phone=phone, comment=comment)
        
        # 2. Формируем блок ИИ, если ответ сгенерирован
        ai_section = ""
        if ai_reply:
            ai_section = f"""
            <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 25px 0; border-radius: 6px;">
                <span style="font-size: 12px; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 8px;">Анализ и моментальный ответ AI:</span>
                <p style="margin: 0; font-style: italic; color: #1e3a8a; font-size: 15px; line-height: 1.6;">"{ai_reply}"</p>
            </div>
            """
        
        # 3. Загружаем и форматируем шаблон для пользователя
        user_template = self._load_template("user_email.html")
        user_html = user_template.format(
            name=name,
            ai_section=ai_section,
            current_year=datetime.now().year
        )
        
        # 4. Безопасно отправляем в пул задач (ошибки сети Render не сломают запрос)
        try:
            await run_in_threadpool(
                self._send_sync_email,
                settings.EMAIL_TO_OWNER,
                "New Portfolio Contact Form Submission",
                owner_html
            )
        except Exception as e:
            logger.error(f"Critical error during owner email thread execution: {str(e)}")

        try:
            await run_in_threadpool(
                self._send_sync_email,
                email,
                "Копия обращения: Портфолио разработчика",
                user_html
            )
        except Exception as e:
            logger.error(f"Critical error during user email thread execution: {str(e)}")