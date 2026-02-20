"""
Employee CRUD Operations
========================
Extends the base CRUD class with Employee-specific queries.
"""

import string
import random
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    """
    CRUD operations for Employee model.
    Inherits standard operations from CRUDBase.
    Adds Employee-specific queries here.
    """
    
    def get_multi_with_relations(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """
        Get multiple employees with eager loading of department and position.
        This prevents N+1 query problem by loading related data in a single query.
        
        Performance:
        - Without eager loading: 1 + N + N queries (1 for employees, N for departments, N for positions)
        - With eager loading: 1 query with LEFT JOINs
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of Employee instances with department and position loaded
        """
        return (
            db.query(self.model)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_id_with_relations(self, db: Session, id: int) -> Optional[Employee]:
        """
        Get a single employee by ID with eager loading of department and position.
        
        Args:
            db: Database session
            id: Employee ID
            
        Returns:
            Employee instance with relations loaded, or None if not found
        """
        return (
            db.query(self.model)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            )
            .filter(self.model.id == id)
            .first()
        )
    
    def get_by_email(self, db: Session, email: str) -> Optional[Employee]:
        """
        Get employee by email.
        
        SQL equivalent: SELECT * FROM employees WHERE email = ?
        
        Useful for lookups and checking for duplicate emails before insert.
        Email must be unique, so this should return at most one record.
        """
        return db.query(Employee).filter(Employee.email == email).first()
    
    def get_by_employee_code(self, db: Session, employee_code: str) -> Optional[Employee]:
        """Get employee by employee code."""
        return db.query(Employee).filter(Employee.employee_code == employee_code).first()
    
    def generate_employee_code(self, db: Session) -> str:
        """
        Generate a unique employee code.
        Format: EMP + 6 digit random number (e.g., EMP123456)
        """
        while True:
            # Generate 6-digit random number
            code_digits = ''.join(random.choices(string.digits, k=6))
            employee_code = f"EMP{code_digits}"
            
            # Check if code already exists
            if not self.get_by_employee_code(db, employee_code):
                return employee_code
    
    def create(self, db: Session, *, obj_in: EmployeeCreate, exclude_fields: set = None) -> Employee:
        """
        Create a new employee with enhanced logic for name fields and employee code generation.
        
        - Combines first_name + last_name into full_name if full_name not provided
        - Auto-generates employee_code if not provided
        - Populates both 'name' and 'full_name' fields for database compatibility
        
        Args:
            db: Database session
            obj_in: EmployeeCreate schema object
            exclude_fields: Set of field names to exclude (e.g., {'password'})
        """
        if exclude_fields:
            obj_in_data = obj_in.model_dump(exclude=exclude_fields, exclude_unset=True)
        else:
            obj_in_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle full_name: use provided full_name or combine first_name + last_name
        if not obj_in_data.get('full_name'):
            first_name = obj_in_data.get('first_name', '').strip()
            last_name = obj_in_data.get('last_name', '').strip()
            obj_in_data['full_name'] = f"{first_name} {last_name}".strip()
        
        # Populate 'name' field with same value as 'full_name' for database compatibility
        obj_in_data['name'] = obj_in_data['full_name']
        
        # Remove first_name and last_name from the data since they're not in the model
        obj_in_data.pop('first_name', None)
        obj_in_data.pop('last_name', None)
        
        # Convert hire_date string to date object if provided
        if obj_in_data.get('hire_date') and isinstance(obj_in_data['hire_date'], str):
            from datetime import datetime
            try:
                obj_in_data['hire_date'] = datetime.strptime(obj_in_data['hire_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                obj_in_data['hire_date'] = None
        
        # Auto-generate employee_code if not provided
        if not obj_in_data.get('employee_code'):
            obj_in_data['employee_code'] = self.generate_employee_code(db)
        
        # Create model instance
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Employee, obj_in: EmployeeUpdate) -> Employee:
        """
        Update an existing employee with enhanced logic for name fields and date fields.
        """
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle full_name: use provided full_name or combine first_name + last_name if they exist
        if obj_data.get('first_name') or obj_data.get('last_name'):
            if not obj_data.get('full_name'):
                # Use existing values if not provided in update
                first_name = obj_data.get('first_name', '').strip() if 'first_name' in obj_data else db_obj.full_name.split(' ', 1)[0]
                last_name = obj_data.get('last_name', '').strip() if 'last_name' in obj_data else (db_obj.full_name.split(' ', 1)[1] if ' ' in db_obj.full_name else '')
                obj_data['full_name'] = f"{first_name} {last_name}".strip()
        
        # Update 'name' field with same value as 'full_name' if full_name is being updated
        if 'full_name' in obj_data:
            obj_data['name'] = obj_data['full_name']
        
        # Remove first_name and last_name from the data since they're not in the model
        obj_data.pop('first_name', None)
        obj_data.pop('last_name', None)
        
        # Convert hire_date string to date object if provided
        if obj_data.get('hire_date') and isinstance(obj_data['hire_date'], str):
            from datetime import datetime
            try:
                obj_data['hire_date'] = datetime.strptime(obj_data['hire_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                obj_data['hire_date'] = None
        
        # Update each field
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Create a global instance to use throughout the app
employee = CRUDEmployee(Employee)
