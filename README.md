# Developer Portfolio Backend API

Асинхронный бэкенд-сервис на базе **FastAPI** для обработки форм обратной связи портфолио-лендинга. Принимает обращения, анализирует тональность через LLM, генерирует персонализированный авто-ответ и отправляет HTML-письма обеим сторонам.

**Live Demo:** `https://your-app.onrender.com` *(заменить после деплоя)*  
**Swagger UI:** `/docs` · **ReDoc:** `/redoc`

---

## 1. Как запустить проект

### Требования

- Python 3.11+
- [Poetry 2.0+](https://python-poetry.org/docs/)
- Gmail-аккаунт с включённой двухфакторной аутентификацией
- API-ключ [Groq](https://console.groq.com) (бесплатный тариф достаточен)

### Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/MakhmudNunu/dev-portfolio-fast-api.git
cd dev-portfolio-fast-api

# 2. Установить зависимости
poetry install

# 3. Создать файл окружения
cp .env.example .env
# Отредактировать .env — заполнить реальные значения (см. раздел ниже)

# 4. Запустить сервер
poetry run python -m app.main
```

Сервер поднимется на `http://127.0.0.1:8000`.  
Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Переменные окружения (`.env`)

```env
PORT=8000
HOST=127.0.0.1
PROJECT_NAME="Developer Portfolio API"

# Gmail SMTP
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your_email@gmail.com"
SMTP_PASSWORD="your_gmail_app_password"   # Пароль приложения, не основной пароль
EMAIL_FROM="your_email@gmail.com"
EMAIL_TO_OWNER="your_email@gmail.com"

# Groq AI (OpenAI-совместимый)
AI_BASE_URL="https://api.groq.com/openai/v1"
AI_API_KEY="your_groq_api_key"
AI_MODEL="llama-3.1-8b-instant"
```

> **Как получить `SMTP_PASSWORD`**: Google-аккаунт → Безопасность → Двухэтапная аутентификация → **Пароли приложений**.

---

## 2. Стек технологий

| Категория | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Фреймворк | FastAPI — async, автовалидация через Pydantic |
| ASGI-сервер | Uvicorn (с hot-reload в dev-режиме) |
| ORM | SQLAlchemy 2.0+ (async-совместимый) |
| База данных | SQLite (файл `database.db` в корне) |
| Валидация | Pydantic v2 + `pydantic-settings` |
| Email | `smtplib` + `run_in_threadpool` (вынос IO в пул потоков) |
| Менеджер пакетов | Poetry 2.0+ |
| **AI-провайдер** | **Groq API** (OpenAI-совместимый SDK) |
| **AI-модель** | **`llama-3.1-8b-instant`** — субсекундный инференс |
| **AI-режим** | **JSON Mode** (`response_format={"type": "json_object"}`) |

---

## 3. Архитектура

### Структура проекта

```
dev-portfolio-fast-api/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── contact.py          # POST /api/contact/ — форма обратной связи
│   │   │   └── system.py           # GET /api/health, GET /api/metrics
│   │   └── schemas/
│   │       └── contact.py          # Pydantic DTO: ContactCreate
│   ├── core/
│   │   ├── config.py               # pydantic-settings: загрузка .env
│   │   └── logger.py               # Двойной хендлер: stdout + data/app.log
│   ├── middlewares/
│   │   └── rate_limiter.py         # In-memory IP tracker, скользящее окно 60с
│   ├── repositories/
│   │   ├── models.py               # SQLAlchemy модель ContactMessage
│   │   └── contact_repository.py   # Data Mapper: create_contact_message_with_ai()
│   ├── services/
│   │   ├── ai_service.py           # Groq API клиент + Graceful Fallback
│   │   ├── contact_service.py      # Оркестратор: AI → DB → Email
│   │   └── email_service.py        # SMTP + HTML-шаблоны
│   ├── templates/
│   │   ├── owner_email.html        # Письмо владельцу с данными формы
│   │   └── user_email.html         # Адаптивное письмо пользователю с AI-ответом
│   ├── database.py                 # SQLAlchemy engine + SessionLocal + Base
│   └── main.py                     # FastAPI app: CORS, Middleware, роутеры
├── data/
│   └── app.log                     # Ротируемый лог (создаётся автоматически)
├── database.db                     # SQLite (создаётся при первом запуске)
├── render.yaml                     # Конфигурация автодеплоя на Render
├── .env.example                    # Шаблон переменных окружения
├── pyproject.toml                  # Poetry 2.0 зависимости
└── README.md
```

### Паттерны и архитектурные решения

**Layered Architecture (Controllers → Services → Repositories)**  
Маршруты (`api/endpoints`) отвечают только за HTTP-протокол. Сервисы (`services`) содержат бизнес-логику. Репозитории (`repositories`) изолируют все SQL-операции. Слои зависят только вниз — это упрощает тестирование и замену реализаций.

**Data Mapper / Repository Pattern**  
Модель `ContactMessage` — чистая структура данных без методов сохранения. Вся работа с БД вынесена в `contact_repository.py`. В отличие от Active Record, логика персистентности не просачивается в бизнес-уровень.

**Dependency Injection через FastAPI**  
`get_db` как `Depends` в эндпоинтах гарантирует корректный lifecycle сессий: сессия открывается на запрос, закрывается после — даже при исключениях.

**Почему FastAPI + SQLite?**  
FastAPI даёт нативный AsyncIO без бойлерплейта, автодокументацию через OpenAPI и валидацию через Pydantic "из коробки". SQLite — zero-configuration: не требует отдельного docker-контейнера на хостинге, что критично для MVP-стадии портфолио.

---

## 4. Реализация API

Все эндпоинты доступны с базовым префиксом `/api`.

### `POST /api/contact/`

Принимает данные формы → запускает AI-анализ → сохраняет в БД → отправляет два письма.

**Rate Limit:** 3 запроса в минуту с одного IP → `429 Too Many Requests`

**Тело запроса:**
```json
{
  "name": "Максим",
  "email": "maxim@example.com",
  "phone": "+79991234567",
  "comment": "Мне нужен сайт-визитка для портфолио. Сроки поджимают."
}
```

**Успешный ответ `201 Created`:**
```json
{
  "success": true,
  "message": "Обращение принято, уведомления отправлены.",
  "data": {
    "id": 1,
    "name": "Максим"
  }
}
```

---

### `GET /api/health`

Liveness/Readiness probe — проверка доступности сервиса.

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-06-20T16:20:00.123456"
}
```

---

### `GET /api/metrics`

Агрегированная статистика из БД, вычисляется динамически через `func.count()`.

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

### Примеры curl-запросов

```bash
# Отправить форму
curl -X POST http://127.0.0.1:8000/api/contact/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Максим","email":"maxim@example.com","phone":"+79991234567","comment":"Хочу заказать лендинг для своего бизнеса."}'

# Проверить статус
curl http://127.0.0.1:8000/api/health

# Получить статистику
curl http://127.0.0.1:8000/api/metrics
```

---

### Валидация и обработка ошибок

**Pydantic-схема `ContactCreate`:**

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `name` | `str` | 2–50 символов |
| `phone` | `str` | 5–20 символов |
| `email` | `EmailStr` | RFC-валидация |
| `comment` | `str` | 10–1000 символов |

Невалидные данные перехватываются **до** запуска бизнес-логики → `422 Unprocessable Entity`.

**Глобальный Exception Handler** в `main.py` — при любой непредвиденной ошибке пишет полный stack trace в лог и возвращает чистый `500 Internal Server Error` вместо падения процесса:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error caught on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
```

---

## 5. AI-интеграция

### Что делает AI

При получении комментария `AIService` асинхронно вызывает `llama-3.1-8b-instant` через Groq API для двух задач одним запросом:

1. **Sentiment Analysis** — определяет тональность (`positive` / `neutral` / `negative`) для приоритизации заявок владельцем.
2. **Auto-reply Generation** — генерирует персонализированный ответ на русском языке, который сразу уходит пользователю на почту.

Используется `response_format={"type": "json_object"}` — JSON Mode — чтобы гарантировать десериализуемый ответ без markdown-обёртки.

### Graceful Fallback

Внешние AI-сервисы могут упасть по трём причинам: превышение Rate Limit, невалидный токен, сетевой таймаут. Приложение реализует безопасную деградацию:

```python
fallback_data = {
    "sentiment": "neutral",
    "reply": "Спасибо за ваше обращение! Я свяжусь с вами в ближайшее время."
}

if not self.client:  # Ключ не задан в .env
    return fallback_data

try:
    response = await self.client.chat.completions.create(
        ...,
        timeout=5.0  # Жёсткий таймаут 5 секунд
    )
    result = json.loads(response.choices[0].message.content)
    if "sentiment" in result and "reply" in result:
        return result
    return fallback_data
except Exception as e:
    logger.error(f"AI Service Error: {str(e)}. Graceful fallback applied.", exc_info=True)
    return fallback_data
```

Если AI падает — форма всё равно отправляется, запись в БД создаётся, письма уходят с нейтральным авто-ответом. Пользователь не видит `500`.

### Системный промпт

```
You are an AI assistant built into a web developer's portfolio website.
Analyze the user's comment and return a JSON object with exactly two keys:
1. 'sentiment': string, strictly one of ['positive', 'neutral', 'negative']
2. 'reply': string, a polite and professional automated reply in Russian addressing the user's comment.
Output ONLY valid JSON. No markdown formatting, no code blocks.
```

---

## 6. Что сделано с помощью AI

### Что генерировал AI

- Архитектурный каркас слоёв (адаптация паттернов NestJS/Spring в плоскость FastAPI).
- Pydantic-схемы валидации (`ContactCreate` с `Field` ограничениями).
- Первоначальную структуру классов `EmailService` и `AIService`.

### Что пришлось исправлять вручную

**Ошибка сериализации в `/health`**  
AI сгенерировал `func.now()` внутри возвращаемого JSON-ответа. Это вызвало `NotImplementedError: Operator 'getitem' is not supported`. Исправлено заменой на `datetime.utcnow().isoformat()`.

**Синтаксис HTML-писем**  
При попытке вставить AI-ответ прямо в f-строку с HTML произошёл конфликт фигурных скобок. Логика была переписана: HTML-шаблоны изолированы в отдельные файлы `owner_email.html` / `user_email.html`, заполнение через безопасный `.format()`.

**Конфигурация Poetry 2.0**  
AI предлагал устаревший флаг `package-mode = false` внутри `[tool.poetry]`. В Poetry 2.0+ с декларативным блоком `[project]` это не нужно — конфиг `pyproject.toml` был приведён к актуальной спецификации.

---

## 7. Хранение данных

### База данных (SQLite)

Все обращения с AI-аналитикой сохраняются в `database.db`. Файл создаётся автоматически при первом запуске через `Base.metadata.create_all()`.

Схема таблицы `contact_messages`:

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | `INTEGER` | Первичный ключ, автоинкремент |
| `name` | `VARCHAR` | Имя отправителя |
| `phone` | `VARCHAR` | Телефон |
| `email` | `VARCHAR` | Email |
| `comment` | `TEXT` | Текст обращения |
| `ai_sentiment` | `VARCHAR` | Тональность от LLM |
| `ai_reply` | `TEXT` | Авто-ответ от LLM |
| `created_at` | `DATETIME` | Время создания |

### Логирование

Реализовано через `logging.basicConfig` с двумя одновременными хендлерами:

- **`StreamHandler`** → `stdout` (реальное время, видно в консоли и в логах платформы Render).
- **`FileHandler`** → `data/app.log` (полная история: метод, путь, статус-код, время выполнения, stack traces).

Директория `data/` создаётся автоматически при старте если не существует.

Пример записи:
```
2026-06-20 16:20:05,123 [INFO] portfolio_backend: Method: POST | Path: /api/contact/ | Status: 201 | Time: 842.17ms
```

### Rate Limiting

Реализован как FastAPI `Depends`-зависимость (`rate_limiter.py`) — in-memory словарь `{ip: [timestamps]}` со скользящим окном 60 секунд:

```
Лимит: 3 запроса / 60 секунд / IP
При превышении: 429 Too Many Requests
Реализация: скользящее окно (устаревшие timestamp'ы вычищаются на каждом запросе)
```

> **Примечание:** In-memory хранение сбрасывается при перезапуске сервиса. Для production рекомендуется Redis.

---

## Деплой на Render

Проект включает готовый `render.yaml`.

**1.** Создать **Web Service** на [render.com](https://render.com) → подключить GitHub-репозиторий.

**2.** Параметры сборки (заполнятся из `render.yaml` автоматически):

| Параметр | Значение |
|----------|----------|
| Language | Python |
| Build Command | `poetry install` |
| Start Command | `poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

**3.** В разделе **Environment Variables** → Bulk Editor — вставить содержимое `.env`, изменив `HOST=127.0.0.1` → `HOST=0.0.0.0`.

**4.** Нажать **Deploy**. После сборки сервис получит публичный URL с SSL-сертификатом.
