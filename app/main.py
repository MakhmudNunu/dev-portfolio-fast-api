from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time

from app.core.config import settings
from app.core.logger import logger
from app.database import engine, Base

from app.api.endpoints.contact import router as contact_router
from app.api.endpoints.system import router as system_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Time: {process_time:.2f}ms"
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error caught on {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal Server Error",
            "detail": "На сервере произошла непредвиденная ошибка!"
        }
    )

app.include_router(contact_router, prefix="/api")
app.include_router(system_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hello World. API is working and SQLite is ready!"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True
    )