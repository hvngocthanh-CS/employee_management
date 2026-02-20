"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    common,
    departments,
    employees,
    positions,
    user,
    salaries,
    attendances,
    leaves,
    statistics
)

api_router = APIRouter()

# Common endpoints (health check, ping, version)
api_router.include_router(
    common.router,
    tags=["Common"]
)

# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Resources
api_router.include_router(
    departments.router,
    prefix="/departments",
    tags=["Departments"]
)

api_router.include_router(
    positions.router,
    prefix="/positions",
    tags=["Positions"]
)

api_router.include_router(
    employees.router,
    prefix="/employees",
    tags=["Employees"]
)

api_router.include_router(
    user.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    salaries.router,
    prefix="/salaries",
    tags=["Salaries"]
)

api_router.include_router(
    attendances.router,
    prefix="/attendances",
    tags=["Attendances"]
)

api_router.include_router(
    leaves.router,
    prefix="/leaves",
    tags=["Leaves"]
)

api_router.include_router(
    statistics.router,
    prefix="/statistics",
    tags=["Statistics"]
)
