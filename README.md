# Developer Portfolio Backend API

Асинхронное серверное приложение на базе **FastAPI** для обработки и интеллектуального анализа форм обратной связи веб-сайта-портфолио. Интегрировано с LLM через Groq API для автоматической оценки тональности обращений и генерации персонализированных ответов. Включает двусторонние адаптивные HTML-уведомления по email.

---

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Фреймворк | FastAPI (AsyncIO, Pydantic-валидация) |
| Менеджер пакетов | Poetry 2.0+ |
| ASGI-сервер | Uvicorn (с hot-reload) |
| ORM / База данных | SQLAlchemy 2.0+ / SQLite |
| Email | `smtplib` + `run_in_threadpool` |
| AI-провайдер | Groq API (OpenAI-совместимый SDK) |
| AI-модель | `llama-3.1-8b-instant` (JSON Mode) |

---

## Архитектура

Приложение построено на **Layered Architecture** с паттернами Dependency Injection и Data Mapper — аналогично подходу NestJS/Spring.

```
dev-portfolio-fast-api/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── contact.py        # Маршруты формы обратной связи
│   │   │   └── system.py         # Health & Metrics эндпоинты
│   │   └── schemas/
│   │       └── contact.py        # Pydantic DTO-схемы
│   ├── core/
│   │   ├── config.py             # pydantic-settings конфигурация
│   │   └── logger.py             # Кастомный логгер
│   ├── database.py               # Инициализация SQLAlchemy-сессий
│   ├── main.py                   # Точка входа, CORS, Middleware
│   ├── repositories/
│   │   ├── contact_repository.py # Data Mapper для работы с БД
│   │   └── models.py             # Декларативные SQLAlchemy-модели
│   ├── services/
│   │   ├── ai_service.py         # Оркестрация запросов к LLM
│   │   ├── contact_service.py    # Координатор бизнес-логики
│   │   └── email_service.py      # Загрузка шаблонов и отправка писем
│   └── templates/
│       ├── owner_email.html      # HTML-письмо для администратора
│       └── user_email.html       # Адаптивный HTML-шаблон для пользователя
├── data/
│   └── app.log                   # Ротируемый лог приложения
├── .env                          # Переменные окружения (не в git)
├── .gitignore
├── pyproject.toml                # Poetry 2.0 конфигурация
└── README.md
```

**Ключевые принципы:**

- **Separation of Concerns** — маршруты отвечают только за HTTP, сервисы изолируют бизнес-логику, репозитории — SQL-запросы.
- **Data Mapper / Repository Pattern** — модели остаются чистыми структурами данных; логика сохранения вынесена в `contact_repository`.
- **FastAPI + SQLite** — максимальная производительность через AsyncIO без бойлерплейта; SQLite как zero-configuration база для MVP без необходимости в Docker.

---

## API Reference

Все эндпоинты доступны с префиксом `/api`.

### `POST /api/contact/`

Принимает данные формы, запускает AI-анализ тональности, отправляет письма и сохраняет запись в БД.

> ⚠️ Rate limit: **3 запроса в минуту** с одного IP (429 Too Many Requests при превышении).

**Тело запроса:**
```json
{
  "name": "Максим",
  "email": "maxim@example.com",
  "phone": "+79991234567",
  "comment": "Мне нужен сайт-визитка для портфолио. Сроки поджимают."
}
```

**Успешный ответ `200 OK`:**
```json
{
  "id": 1,
  "name": "Максим",
  "email": "maxim@example.com",
  "phone": "+79991234567",
  "comment": "Мне нужен сайт-визитка для портфолио. Сроки поджимают.",
  "ai_sentiment": "positive",
  "ai_reply": "Здравствуйте, Максим! Спасибо за интерес к моим услугам...",
  "created_at": "2026-06-20T16:20:00"
}
```

---

### `GET /api/health`

Liveness/Readiness probe. Возвращает состояние подключения к БД и серверное время в ISO-формате.

---

### `GET /api/metrics`

Агрегированная статистика обращений, вычисляемая динамически из БД.

```json
{
  "total_submissions": 42,
  "ai_sentiment_breakdown": {
    "positive": 25,
    "neutral": 12,
    "negative": 5
  }
}
```

---

## Валидация и обработка ошибок

- **Pydantic-валидация** — невалидный email или пустые поля перехватываются до запуска бизнес-логики → `422 Unprocessable Entity`.
- **Глобальный Exception Handler** — любая непредвиденная ошибка пишет полный Stack Trace в лог и возвращает чистый `500 Internal Server Error`.

---

## AI-интеграция и Graceful Fallback

При получении комментария `AIService` асинхронно вызывает модель `llama-3.1-8b-instant` для двух задач:

1. **Sentiment Analysis** — определение тональности (`positive` / `neutral` / `negative`) для приоритизации заявок.
2. **Auto-reply Generation** — мгновенный персонализированный ответ, который уходит пользователю на почту.

При сбое внешнего API (Rate Limit, невалидный токен, таймаут) приложение не падает — используются дефолтные значения:

```python
except Exception as e:
    logger.error(f"AI Service Failure: {str(e)}")
    return {
        "sentiment": "neutral",
        "reply": "Спасибо за ваше обращение! Я получил его и свяжусь с вами в ближайшее время."
    }
```

**Системный промпт для LLM:**
> *"You are an AI assistant for a full-stack developer portfolio. Analyze the user's comment. Respond strictly in JSON format with two fields: 'sentiment' (choose exactly one from: 'positive', 'neutral', 'negative') and 'reply' (a professional, friendly response to the user in Russian based on their comment). Do not include any markdown formatting, headers, or code blocks outside of the raw JSON."*

---

## Логирование и Rate Limiting

**Логирование** — два параллельных потока:
- `stdout` — для локальной отладки в реальном времени.
- `data/app.log` — полная история: HTTP-метод, путь, статус-код, время выполнения, трейсы ошибок.

**Rate Limiting** — кастомный Middleware на базе скользящего окна времени (In-Memory IP tracking). Лимит: **3 запроса/мин** на один IP → `429 Too Many Requests`.

**Статистика** вычисляется динамически через `func.count()` в SQLAlchemy — без хранения в RAM, без потери данных при перезапуске.

---

## Локальная установка

**1. Клонировать репозиторий и установить зависимости:**

```bash
git clone https://github.com/MakhmudNunu/dev-portfolio-fast-api.git
cd dev-portfolio-fast-api
poetry install
```

**2. Создать файл `.env` в корне проекта:**

```env
PORT=8000
HOST=127.0.0.1
PROJECT_NAME="Developer Portfolio API"

SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your_email@gmail.com"
SMTP_PASSWORD="your_gmail_app_password"
EMAIL_FROM="your_email@gmail.com"
EMAIL_TO_OWNER="your_email@gmail.com"

AI_BASE_URL="https://api.groq.com/openai/v1"
AI_API_KEY="your_groq_api_key"
AI_MODEL="llama-3.1-8b-instant"
```

> 💡 `SMTP_PASSWORD` — это [пароль приложения Google](https://myaccount.google.com/apppasswords), не основной пароль аккаунта.

**3. Запустить сервер:**

```bash
poetry run python -m app.main
```

Swagger UI доступен по адресу: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Деплой на Render

**1.** Создать **Web Service** на [render.com](https://render.com) и подключить GitHub-репозиторий.

**2.** Параметры сборки:

| Параметр | Значение |
|----------|----------|
| Language | Python |
| Build Command | `poetry install` |
| Start Command | `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

**3.** В разделе **Environment Variables** вставить содержимое `.env` через Bulk Editor.

> ⚠️ Обязательно изменить `HOST` с `127.0.0.1` на `0.0.0.0` — иначе Render не сможет перенаправлять трафик на порт приложения.

**4.** Нажать **Deploy Web Service**. После сборки приложение получит публичный URL с SSL-сертификатом.
