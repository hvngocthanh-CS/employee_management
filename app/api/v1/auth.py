from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, Token, UserProfile, ChangePasswordRequest, ResetPasswordRequest
from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.permissions import get_user_permissions, get_menu_permissions, PermissionDependencies

router = APIRouter()


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Login với email (employee) hoặc username (admin/manager) - return JWT token với user info
    """
    from app.models.employee import Employee
    
    user = None
    identifier = user_in.identifier.strip()
    
    # Nếu identifier có @, coi như email -> tìm employee trước
    if '@' in identifier:
        # Login bằng email (cho employee)
        employee = db.query(Employee).filter(Employee.email == identifier).first()
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        # Tìm user liên kết với employee
        user = db.query(User).filter(User.employee_id == employee.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No account found for this email",
            )
    else:
        # Login bằng username (cho admin/manager)
        user = db.query(User).filter(User.username == identifier).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
    
    # Verify password
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Get user permissions and menu visibility
    permissions = get_user_permissions(user)
    menu_permissions = get_menu_permissions(user)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "employee_id": user.employee_id,
            "is_active": user.is_active,
            "permissions": permissions,
            "menu_permissions": menu_permissions
        }
    }


@router.get("/me", response_model=UserProfile)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile với permissions
    """
    # Get user permissions and menu visibility
    permissions = get_user_permissions(current_user)
    menu_permissions = get_menu_permissions(current_user)
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        employee_id=current_user.employee_id,
        is_active=current_user.is_active,
        permissions=permissions,
        menu_permissions=menu_permissions,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/register")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register new admin or manager account.
    Employee accounts MUST be created by admin/manager through /api/v1/users/ endpoint.
    """
    from app.core.security import get_password_hash
    
    # Chặn đăng ký với role EMPLOYEE
    if user_in.role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee accounts cannot be self-registered. Please contact your admin or manager."
        )
    
    # Chỉ cho phép ADMIN và MANAGER tự đăng ký
    if user_in.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role for registration"
        )
    
    # Kiểm tra username đã tồn tại?
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Tạo user mới với password hashed và role (không có employee_id)
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        hashed_password=hashed_password,
        role=user_in.role,
        employee_id=None,  # Admin/Manager không cần employee_id
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Account registered successfully",
        "username": new_user.username,
        "role": new_user.role.value,
        "id": new_user.id
    }


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change password for current user (employee can change their own password).
    
    Permissions: All authenticated users
    
    Request Body:
      {
        "current_password": "old_password123",
        "new_password": "new_password456"
      }
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {
        "message": "Password changed successfully"
    }


@router.post("/reset-password")
def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(PermissionDependencies.can_update_user)
):
    """
    Reset password for any user (Admin only).
    
    Permissions: Admin only
    
    Request Body:
      {
        "user_id": 5,
        "new_password": "reset_password123"
      }
      
    Use case: When employee forgets password or admin wants to reset it.
    """
    # Find the target user
    target_user = db.query(User).filter(User.id == reset_data.user_id).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {reset_data.user_id} not found"
        )
    
    # Update password
    target_user.hashed_password = get_password_hash(reset_data.new_password)
    db.commit()
    
    return {
        "message": f"Password reset successfully for user: {target_user.username}",
        "user_id": target_user.id,
        "username": target_user.username
    }
