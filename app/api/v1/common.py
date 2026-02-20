"""
Common API Endpoints
====================
Chứa các endpoints chung như health check, ping, version info, etc.
Không nên tạo file riêng cho từng endpoint nhỏ này.
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health_check", response_class=PlainTextResponse)
def health_check():
    """
    Simple health check endpoint.
    Returns OK if the API is running.
    """
    return "OK"


@router.get("/ping")
def ping():
    """
    Ping endpoint to check API availability.
    Returns current server time and status.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Employee Management API is running"
    }


@router.get("/version")
def get_version():
    """
    Get API version information.
    """
    return {
        "version": "1.0.0",
        "api": "v1",
        "service": "Employee Management System"
    }
