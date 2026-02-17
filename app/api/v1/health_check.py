"""
Health Check API
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/health_check", response_class=PlainTextResponse)
def health_check():
    """Simple health check endpoint"""
    return "OK"
