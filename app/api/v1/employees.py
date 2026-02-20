"""
Employee API Router
===================
Endpoints for managing employees with role-based permissions.

Roles:
  - Admin: Full CRUD permissions
  - Manager: Can view and edit employees
  - Employee: Can only view their own information
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.crud import employee as crud_employee
from app.core.permissions import PermissionDependencies, check_resource_ownership
from app.core.deps import get_current_user
from app.models.user import User

# Setup logger
logger = logging.getLogger(__name__)

# Create router for employee endpoints
router = APIRouter()


def enhance_employee_response(employee) -> dict:
    """
    Convert Employee model to enhanced response with first_name/last_name split
    and additional fields for frontend compatibility
    """
    # Split full_name into first_name and last_name
    name_parts = employee.full_name.split(' ', 1) if employee.full_name else ['', '']
    first_name = name_parts[0] if len(name_parts) > 0 else ''
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Format hire_date as string if it exists
    hire_date_str = None
    if employee.hire_date:
        hire_date_str = employee.hire_date.isoformat() if hasattr(employee.hire_date, 'isoformat') else str(employee.hire_date)
    
    # Convert salary to float if it exists
    salary_float = float(employee.salary) if employee.salary else None
    
    return {
        'id': employee.id,
        'full_name': employee.full_name,
        'first_name': first_name,
        'last_name': last_name,
        'employee_code': employee.employee_code,
        'email': employee.email,
        'phone': employee.phone,
        'department_id': employee.department_id,
        'position_id': employee.position_id,
        'hire_date': hire_date_str,
        'salary': salary_float,
        'department_name': getattr(employee.department, 'name', None) if hasattr(employee, 'department') and employee.department else None,
        'position_title': getattr(employee.position, 'title', None) if hasattr(employee, 'position') and employee.position else None,
    }


@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, min_length=2, max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_employee)
):
    """
    Get all employees (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Query Parameters:
      skip: Number of records to skip for pagination (default: 0)
      limit: Maximum records to return (default: 100)
      search: Search term for employee_code, full_name, or email (min 2 chars)
      
    Returns:
      List of employees with full information including department and position names
    
    Performance Note:
      Uses eager loading to prevent N+1 query problem
    """
    if search:
        # Search mode: filter by employee_code, full_name, or email
        from app.models.employee import Employee
        query = db.query(Employee)
        search_term = f"%{search}%"
        query = query.filter(
            (Employee.employee_code.ilike(search_term)) |
            (Employee.full_name.ilike(search_term)) |
            (Employee.email.ilike(search_term))
        )
        # Apply eager loading
        from sqlalchemy.orm import joinedload
        query = query.options(
            joinedload(Employee.department),
            joinedload(Employee.position)
        )
        employees = query.offset(skip).limit(limit).all()
    else:
        # Normal list mode: use optimized query
        employees = crud_employee.get_multi_with_relations(db, skip=skip, limit=limit)
    
    # Convert to enhanced response format
    enhanced_employees = [enhance_employee_response(emp) for emp in employees]
    return enhanced_employees


@router.get("/me", response_model=EmployeeResponse)
def get_my_employee_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's employee data.
    
    Permissions: All authenticated users
    
    Returns:
      Current user's employee information
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for this user"
        )
    
    employee = crud_employee.get(db, id=current_user.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    return employee


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_in: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_create_employee)
):
    """
    Create a new employee with user account (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Request Body:
      {
        "first_name": "John",
        "last_name": "Doe", 
        "email": "john@example.com",
        "password": "initial123",
        "phone": "+1234567890",
        "department_id": 1,
        "position_id": 1,
        "hire_date": "2024-01-01",
        "salary": 50000.00
      }
      
    Note: 
      - Automatically creates a user account for the employee
      - employee_code will be auto-generated if not provided
      - Either provide full_name OR both first_name and last_name
      - first_name + last_name will be combined into full_name
      
    Validation:
      - email must be unique
      - email must be a valid email format
      - password must be at least 6 characters
      - Either full_name OR (first_name AND last_name) is required
      
    Returns:
      The created employee with auto-generated id and employee_code
    """
    from app.models.user import UserRole
    from app.core.security import get_password_hash
    from app.crud.user import user as crud_user
    
    logger.info(f"Creating new employee: {employee_in.email}")
    
    # Check if email already exists
    existing = crud_employee.get_by_email(db, email=employee_in.email)
    if existing:
        logger.warning(f"Create employee failed: Email '{employee_in.email}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{employee_in.email}' is already registered"
        )
    
    # Create the employee first (exclude password field - not needed for employee table)
    try:
        employee = crud_employee.create(db, obj_in=employee_in, exclude_fields={'password'})
        logger.info(f"Employee created: ID={employee.id}, Code={employee.employee_code}, Email={employee.email}")
    except Exception as e:
        logger.error(f"Failed to create employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create employee: {str(e)}"
        )
    
    # Create user account for the employee
    try:
        # Generate username from email (before @)
        username = employee_in.email.split('@')[0]
        
        # Check if username already exists, add suffix if needed
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            username = f"{username}_{employee.id}"
        
        # Create user with EMPLOYEE role
        new_user = User(
            username=username,
            hashed_password=get_password_hash(employee_in.password),
            role=UserRole.EMPLOYEE,
            employee_id=employee.id,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User account created for employee: username={username}, employee_id={employee.id}")
    except Exception as e:
        # Rollback employee creation if user creation fails
        logger.error(f"Failed to create user account for employee {employee.id}: {str(e)}")
        db.delete(employee)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user account: {str(e)}"
        )
    
    # Return enhanced response format
    return enhance_employee_response(employee)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_own_employee_data)
):
    """
    Get a single employee by ID.
    
    Permissions: 
      - Admin/Manager: Can view any employee
      - Employee: Can only view own record
      
    Path Parameters:
      employee_id: The employee's primary key
      
    Returns:
      Employee data hoặc 403 if no permission, 404 if not found
    """
    # Check if user can access this employee record
    if not check_resource_ownership(current_user, employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own employee record"
        )
    
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )
    
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_in: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_update_employee)
):
    """
    Update an employee (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Path Parameters:
      employee_id: The employee's primary key
      
    Request Body:
      {
        "first_name": "Jane",  // optional
        "last_name": "Smith",  // optional
        "email": "jane.smith@example.com",  // optional
        "phone": "+0987654321",  // optional
        "department_id": 2,  // optional
        "position_id": 2,  // optional
        "salary": 55000.00  // optional
      }
      
    Returns:
      Updated employee data
    """
    # Check if employee exists
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )
    
    # Check email uniqueness if email is being updated
    if employee_in.email and employee_in.email != employee.email:
        existing = crud_employee.get_by_email(db, email=employee_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{employee_in.email}' is already registered"
            )
    
    # Update employee
    employee = crud_employee.update(db, db_obj=employee, obj_in=employee_in)
    # Return enhanced response format
    return enhance_employee_response(employee)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_delete_employee)
):
    """
    Delete an employee and their user account (Admin only).
    
    Permissions: Admin only
    
    Path Parameters:
      employee_id: The employee's primary key
      
    Returns:
      204 No Content on success, 404 if not found
      
    Note: 
      - This will also delete the associated user account
      - Consider soft delete for production use
    """
    logger.info(f"Deleting employee: ID={employee_id}")
    
    # Check if employee exists
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        logger.warning(f"Delete employee failed: Employee {employee_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found"
        )
    
    employee_code = employee.employee_code
    employee_email = employee.email
    
    # Delete associated user account first (if exists)
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if user:
        logger.info(f"Deleting user account: username={user.username}, employee_id={employee_id}")
        db.delete(user)
        db.commit()
    
    # Delete employee
    crud_employee.remove(db, id=employee_id)
    logger.info(f"Employee deleted successfully: ID={employee_id}, Code={employee_code}, Email={employee_email}")
    return None


@router.get("/search/{query}", response_model=List[EmployeeResponse])
def search_employees(
    query: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_read_employee)
):
    """
    Search employees by name or email (Admin/Manager only).
    
    Permissions: Admin, Manager
    
    Path Parameters:
      query: Search term (name hoặc email)
      
    Query Parameters:
      skip: Number of records to skip
      limit: Maximum records to return
      
    Returns:
      List of matching employees
    """
    employees = crud_employee.search(db, query=query, skip=skip, limit=limit)
    return employees


@router.get("/me", response_model=EmployeeResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's employee profile.
    
    Permissions: All authenticated users with employee_id
    
    Returns:
      Current user's employee data
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for current user"
        )
    
    employee = crud_employee.get(db, id=current_user.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee record not found"
        )
    
    # Return enhanced response format
    return enhance_employee_response(employee)
