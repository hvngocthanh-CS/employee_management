"""Remove salary column from employees table

Revision ID: remove_employee_salary
Revises: add_salary_data
Create Date: 2026-02-21

EXPLAINING THE CHANGE:
======================
PROBLEM: We have 2 places storing salary data:
  1. employees.salary (DECIMAL column) - OLD DESIGN ❌
  2. salaries table (separate table) - CORRECT DESIGN ✅

This violates Database Normalization principles:
  - Data duplication (which salary is correct?)
  - No history tracking in employees.salary
  - Confusing: employee.salary != current salary in salaries table

SOLUTION: Remove employees.salary column completely
  - Only use salaries table for ALL salary data
  - Use relationship: Employee.salaries (One-to-Many)
  - Query current salary: JOIN salaries WHERE effective_to IS NULL

DATABASE DESIGN PRINCIPLE:
=========================
BAD DESIGN (Before):
  employees
    ├── id (PK)
    ├── name
    ├── salary ❌ (duplicate data, no history)
    └── ...
  
  salaries
    ├── id (PK)
    ├── employee_id (FK) → employees.id
    ├── base_salary
    ├── effective_from
    └── effective_to

GOOD DESIGN (After):
  employees
    ├── id (PK)
    ├── name
    └── ... (NO salary column!)
  
  salaries (SINGLE SOURCE OF TRUTH)
    ├── id (PK)
    ├── employee_id (FK) → employees.id CASCADE DELETE
    ├── base_salary
    ├── effective_from
    └── effective_to (NULL = current salary)

SQL TO GET CURRENT SALARY:
=========================
SELECT e.id, e.full_name, s.base_salary as current_salary
FROM employees e
LEFT JOIN salaries s ON s.employee_id = e.id 
  AND s.effective_to IS NULL
ORDER BY e.id;

RELATIONSHIP IN SQLAlchemy:
===========================
class Employee(Base):
    # ... other fields
    salaries = relationship("Salary", back_populates="employee")
    
    # Property to get current salary
    @property
    def current_salary(self):
        current = [s for s in self.salaries if s.effective_to is None]
        return current[0].base_salary if current else None

class Salary(Base):
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))
    employee = relationship("Employee", back_populates="salaries")
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_employee_salary'
down_revision = 'add_salary_data'
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove salary column from employees table.
    Data is now ONLY in salaries table (proper design).
    """
    print("⚠️  Removing employees.salary column...")
    print("ℹ️  Salary data now ONLY in salaries table (proper Foreign Key design)")
    
    # Drop the salary column
    op.drop_column('employees', 'salary')
    
    print("✅ employees.salary column removed")
    print("ℹ️  Use LEFT JOIN with salaries table to get current salary")


def downgrade():
    """
    Add salary column back (only if you need to rollback).
    Note: This is for reversibility only. The correct design is WITHOUT this column.
    """
    op.add_column('employees', 
        sa.Column('salary', sa.DECIMAL(10, 2), nullable=True)
    )
    
    # Optionally copy current salary from salaries table back to employees
    # (this is just for rollback, not recommended in production)
    print("⚠️  Rollback: Added salary column back (not recommended)")
