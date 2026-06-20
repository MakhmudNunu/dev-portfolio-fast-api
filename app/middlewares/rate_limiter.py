from fastapi import Request, HTTPException, status
import time

CLIENTS_REQUESTS = {}

RATE_LIMIT_WINDOW = 60 
RATE_LIMIT_MAX_REQUESTS = 3

async def rate_limiter(request: Request):
    client_ip = request.headers.get("x-forwarded-for") or request.client.host
    current_time = time.time()

    if client_ip not in CLIENTS_REQUESTS:
        CLIENTS_REQUESTS[client_ip] = []

    CLIENTS_REQUESTS[client_ip] = [
        req_time for req_time in CLIENTS_REQUESTS[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    if len(CLIENTS_REQUESTS[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов. Пожалуйста, подождите минуту перед повторной отправкой формы."
        )

    CLIENTS_REQUESTS[client_ip].append(current_time)