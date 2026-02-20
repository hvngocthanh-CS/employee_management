from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import PermissionDependencies
from app.models.user import User, UserRole
from app.models.leave import LeaveStatus, Leave
from app.schemas.leave import (
    LeaveCreate,
    LeaveUpdate,
    LeaveApproval,
    LeaveCancel,
    LeaveResponse,
    LeaveListResponse,
    LeaveBalance,
    LeaveStatistics,
    LeaveCalendar
)
from app.crud import leave as crud_leave, employee as crud_employee

router = APIRouter()


@router.get("/", response_model=LeaveListResponse)
def list_leaves(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    status: Optional[LeaveStatus] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all leaves
    Admin/Manager: xem tất cả
    Employee: chỉ xem của mình
    """
    if current_user.role == UserRole.EMPLOYEE:
        # Employee chỉ xem leaves của mình
        leaves = crud_leave.get_by_employee(
            db,
            employee_id=current_user.employee_id,
            status=status,
            skip=skip,
            limit=limit
        )
        # Count total for employee
        count_query = db.query(Leave).filter(Leave.employee_id == current_user.employee_id)
        if status:
            count_query = count_query.filter(Leave.status == status)
        total = count_query.count()
    else:
        # Admin/Manager xem tất cả
        query = db.query(Leave)
        if status:
            query = query.filter(Leave.status == status)
        
        total = query.count()
        leaves = query.order_by(Leave.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    # Convert to response format
    leave_responses = []
    for leave in leaves:
        employee = crud_employee.get(db, id=leave.employee_id)
        approver_name = None
        if leave.approved_by:
            from app.crud import user as crud_user
            approver = crud_user.get(db, id=leave.approved_by)
            if approver and approver.employee:
                approver_name = approver.employee.full_name
        
        leave_responses.append(
            LeaveResponse(
                **leave.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None,
                approver_name=approver_name
            )
        )
    
    return LeaveListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        leaves=leave_responses
    )


@router.get("/pending", response_model=List[LeaveResponse])
def get_pending_leaves(
    *,
    db: Session = Depends(get_db),
    department_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    current_user: User = Depends(PermissionDependencies.can_read_leave)
):
    """
    Get pending leave requests
    Permissions: Admin, Manager
    """
    leaves = crud_leave.get_pending_leaves(
        db, department_id=department_id, skip=skip, limit=limit
    )
    
    result = []
    for leave in leaves:
        employee = crud_employee.get(db, id=leave.employee_id)
        result.append(
            LeaveResponse(
                **leave.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None
            )
        )
    
    return result


@router.get("/my-leaves", response_model=LeaveListResponse)
def get_my_leaves(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    status: Optional[LeaveStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's leave requests.
    
    Permissions: All authenticated users with employee_id
    
    Query Parameters:
      skip: Number of records to skip
      limit: Maximum records to return
      status: Filter by leave status
      
    Returns:
      List of current user's leave requests
    """
    if not current_user.employee_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employee record found for current user"
        )
    
    # Get employee leaves
    leaves = crud_leave.get_by_employee(
        db,
        employee_id=current_user.employee_id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    # Get total count
    count_query = db.query(Leave).filter(Leave.employee_id == current_user.employee_id)
    if status:
        count_query = count_query.filter(Leave.status == status)
    total = count_query.count()
    
    # Add employee info to response
    employee = crud_employee.get(db, id=current_user.employee_id)
    result = []
    for leave in leaves:
        leave_dict = leave.__dict__.copy()
        leave_dict['employee_name'] = employee.full_name if employee else None
        leave_dict['employee_code'] = employee.employee_code if employee else None
        leave_dict['department_name'] = employee.department.name if employee and employee.department else None
        result.append(LeaveResponse(**leave_dict))
    
    return LeaveListResponse(
        leaves=result, 
        total=total,
        page=skip // limit + 1,  # Calculate current page (1-based)
        page_size=limit
    )


@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get leave by ID"""
    leave = crud_leave.get(db, id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found"
        )
    
    # Check permission
    if current_user.role == UserRole.EMPLOYEE:
        if leave.employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own leave requests"
            )
    
    employee = crud_employee.get(db, id=leave.employee_id)
    
    approver_name = None
    if leave.approved_by:
        from app.crud import user as crud_user
        approver = crud_user.get(db, id=leave.approved_by)
        if approver and approver.employee:
            approver_name = approver.employee.full_name
    
    return LeaveResponse(
        **leave.__dict__,
        employee_name=employee.full_name if employee else None,
        employee_code=employee.employee_code if employee else None,
        department_name=employee.department.name if employee and employee.department else None,
        approver_name=approver_name
    )


@router.post("/", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
def create_leave(
    *,
    db: Session = Depends(get_db),
    leave_in: LeaveCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Tạo đơn nghỉ phép
    Employee chỉ được tạo cho chính mình
    """
    # Check employee exists
    employee = crud_employee.get(db, id=leave_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Validate: start_date must be >= employee hire_date
    if employee.hire_date and leave_in.start_date < employee.hire_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ngày bắt đầu nghỉ phép ({leave_in.start_date}) phải >= ngày thuê nhân viên ({employee.hire_date})"
        )
    
    # Employee chỉ được tạo leave cho chính mình
    if current_user.role == UserRole.EMPLOYEE:
        if leave_in.employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create leave requests for yourself"
            )
    
    # Check for conflicts
    has_conflict = crud_leave.check_leave_conflict(
        db,
        employee_id=leave_in.employee_id,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date
    )
    
    if has_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave request conflicts with existing leave"
        )
    
    leave = crud_leave.create(db, obj_in=leave_in)
    
    return LeaveResponse(
        **leave.__dict__,
        employee_name=employee.full_name,
        employee_code=employee.employee_code,
        department_name=employee.department.name if employee.department else None
    )


@router.put("/{leave_id}", response_model=LeaveResponse)
def update_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    leave_in: LeaveUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update leave request (chỉ khi status = PENDING)
    Employee chỉ được update của mình
    """
    leave = crud_leave.get(db, id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found"
        )
    
    # Check permission
    if current_user.role == UserRole.EMPLOYEE:
        if leave.employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own leave requests"
            )
    
    # Chỉ update được khi PENDING
    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update leave with status: {leave.status}"
        )
    
    # Check conflicts if updating dates
    if leave_in.start_date or leave_in.end_date:
        start = leave_in.start_date or leave.start_date
        end = leave_in.end_date or leave.end_date
        
        has_conflict = crud_leave.check_leave_conflict(
            db,
            employee_id=leave.employee_id,
            start_date=start,
            end_date=end,
            exclude_leave_id=leave_id
        )
        
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave request conflicts with existing leave"
            )
    
    leave = crud_leave.update(db, db_obj=leave, obj_in=leave_in)
    
    employee = crud_employee.get(db, id=leave.employee_id)
    
    return LeaveResponse(
        **leave.__dict__,
        employee_name=employee.full_name if employee else None,
        employee_code=employee.employee_code if employee else None,
        department_name=employee.department.name if employee and employee.department else None
    )


@router.post("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(PermissionDependencies.can_approve_leave)
):
    """
    Approve leave request
    Permissions: Admin, Manager
    """
    try:
        leave = crud_leave.approve_leave(
            db, leave_id=leave_id, approver_id=current_user.id
        )
        
        employee = crud_employee.get(db, id=leave.employee_id)
        
        return LeaveResponse(
            **leave.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None,
            approver_name=current_user.employee.full_name if current_user.employee else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(PermissionDependencies.can_approve_leave)
):
    """
    Reject leave request
    Permissions: Admin, Manager
    """
    try:
        leave = crud_leave.reject_leave(
            db, leave_id=leave_id, approver_id=current_user.id
        )
        
        employee = crud_employee.get(db, id=leave.employee_id)
        
        return LeaveResponse(
            **leave.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None,
            approver_name=current_user.employee.full_name if current_user.employee else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{leave_id}/cancel", response_model=LeaveResponse)
def cancel_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(get_current_user)
):
    """Hủy đơn nghỉ phép (employee tự hủy)"""
    try:
        leave = crud_leave.cancel_leave(
            db, leave_id=leave_id, employee_id=current_user.employee_id
        )
        
        employee = crud_employee.get(db, id=leave.employee_id)
        
        return LeaveResponse(
            **leave.__dict__,
            employee_name=employee.full_name if employee else None,
            employee_code=employee.employee_code if employee else None,
            department_name=employee.department.name if employee and employee.department else None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/balance/{employee_id}", response_model=LeaveBalance)
def get_leave_balance(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    year: int = Query(default_factory=lambda: date.today().year),
    current_user: User = Depends(get_current_user)
):
    """Get số ngày phép còn lại"""
    # Check permission
    if current_user.role == UserRole.EMPLOYEE:
        if employee_id != current_user.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own leave balance"
            )
    
    employee = crud_employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    balance = crud_leave.get_leave_balance(
        db, employee_id=employee_id, year=year
    )
    
    return LeaveBalance(
        employee_id=employee_id,
        employee_name=employee.full_name,
        year=year,
        **balance
    )


@router.get("/statistics/monthly", response_model=LeaveStatistics)
def get_leave_statistics(
    *,
    db: Session = Depends(get_db),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    department_id: Optional[int] = None,
    current_user: User = Depends(PermissionDependencies.can_read_leave)
):
    """
    Get monthly leave statistics
    Permissions: Admin, Manager
    """
    stats = crud_leave.get_leave_statistics(
        db, month=month, year=year, department_id=department_id
    )
    
    return LeaveStatistics(**stats)


@router.get("/calendar/{target_date}", response_model=LeaveCalendar)
def get_leave_calendar(
    *,
    db: Session = Depends(get_db),
    target_date: date,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Lịch nghỉ phép trong một ngày"""
    calendar = crud_leave.get_leave_calendar(
        db, target_date=target_date, department_id=department_id
    )
    
    # Convert leaves to response format
    leave_responses = []
    for leave in calendar["leaves"]:
        employee = crud_employee.get(db, id=leave.employee_id)
        leave_responses.append(
            LeaveResponse(
                **leave.__dict__,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                department_name=employee.department.name if employee and employee.department else None
            )
        )
    
    return LeaveCalendar(
        date=target_date,
        total_on_leave=calendar["total_on_leave"],
        leaves=leave_responses
    )


@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: int,
    current_user: User = Depends(PermissionDependencies.can_delete_leave)
):
    """
    Delete leave request (hard delete)
    Permissions: Admin only
    Note: Should use cancel instead of delete in most cases
    """
    leave = crud_leave.get(db, id=leave_id)
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave not found"
        )
    
    crud_leave.delete(db, id=leave_id)
    return None
