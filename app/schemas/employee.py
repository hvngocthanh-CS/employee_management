"""
Employee Schemas
================
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional
from datetime import date
import re


class EmployeeCreate(BaseModel):
    """Schema for creating a new employee."""
    # Support both full_name (legacy) and first_name/last_name (current frontend)
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Employee full name (optional if first_name/last_name provided)"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Employee first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Employee last name"
    )
    employee_code: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Employee code (auto-generated if not provided)"
    )
    email: EmailStr = Field(
        ...,
        description="Employee email (must be unique)"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Initial password for employee account (minimum 6 characters)"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Employee phone number"
    )
    department_id: Optional[int] = Field(
        None,
        description="Department ID (foreign key)"
    )
    position_id: Optional[int] = Field(
        None,
        description="Position ID (foreign key)"
    )
    hire_date: Optional[date] = Field(
        None,
        description="Hire date (YYYY-MM-DD)"
    )
    salary: Optional[float] = Field(
        None,
        description="Salary (ignored for now, future enhancement)"
    )
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format (basic check)"""
        if v and not re.match(r'^[0-9+\-\s()]{8,20}$', v):
            raise ValueError('Số điện thoại không hợp lệ (8-20 chữ số, có thể có +, -, khoảng trắng, dấu ngoặc)')
        return v
    
    @field_validator('hire_date')
    @classmethod
    def validate_hire_date(cls, v):
        """Hire date must not be in the future"""
        if v and v > date.today():
            raise ValueError('Ngày thuê không được trong tương lai')
        return v
    
    @model_validator(mode='after')
    def validate_name_fields(self):
        """Ensure either full_name is provided OR both first_name and last_name are provided."""
        if not self.full_name and not (self.first_name and self.last_name):
            raise ValueError("Either 'full_name' or both 'first_name' and 'last_name' must be provided")
        return self


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Employee full name (optional if first_name/last_name provided)"
    )
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Employee first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Employee last name"
    )
    employee_code: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="Employee code"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Employee email"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Employee phone number"
    )
    department_id: Optional[int] = Field(
        None,
        description="Department ID"
    )
    position_id: Optional[int] = Field(
        None,
        description="Position ID"
    )
    hire_date: Optional[date] = Field(
        None,
        description="Hire date (YYYY-MM-DD format)"
    )
    salary: Optional[float] = Field(
        None,
        description="Salary amount"
    )
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v and not re.match(r'^[0-9+\-\s()]{8,20}$', v):
            raise ValueError('Số điện thoại không hợp lệ')
        return v
    
    @field_validator('hire_date')
    @classmethod
    def validate_hire_date(cls, v):
        """Hire date must not be in the future"""
        if v and v > date.today():
            raise ValueError('Ngày thuê không được trong tương lai')
        return v


class EmployeeResponse(BaseModel):
    """Schema for returning employee data from the API."""
    id: int
    full_name: str
    first_name: str = ""
    last_name: str = ""
    employee_code: str
    email: str
    phone: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    hire_date: Optional[date] = None
    salary: Optional[float] = None
    
    # Related data (optional)
    department_name: Optional[str] = None
    position_title: Optional[str] = None
    
    class Config:
        from_attributes = True
