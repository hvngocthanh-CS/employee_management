"""
FastAPI Main Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
from app.database import engine, Base
import time

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Employee Management System API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every incoming request and response"""
    response = await call_next(request)
    return response


# Create database tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


create_tables()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Employee Management System API",
        "version": settings.VERSION,
        "docs": "http://localhost:8000/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
