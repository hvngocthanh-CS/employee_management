"""Remove salary column from employees table

Revision ID: 003
Revises: 002
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
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove salary column from employees table.
    
    IMPORTANT: Run migration 002 (add_salary_data) first to ensure
    all employees have salary records in the salaries table before
    removing the salary column from employees table.
    """
    # Drop the salary column
    # Note: In production, you might want to:
    # 1. First copy data from employees.salary to salaries table
    # 2. Then drop the column
    # But we already did step 1 in migration 002
    op.drop_column('employees', 'salary')
    
    print("✓ Removed salary column from employees table")
    print("  All salary data now in 'salaries' table only")


def downgrade():
    """
    Restore salary column to employees table.
    
    WARNING: This will re-add the column but it will be NULL for all employees.
    You would need another data migration to populate it from salaries table.
    """
    op.add_column('employees',
        sa.Column('salary', sa.DECIMAL(precision=10, scale=2), nullable=True)
    )
    
    print("✓ Restored salary column to employees table")
    print("  WARNING: Column values are NULL, need data migration to populate")
