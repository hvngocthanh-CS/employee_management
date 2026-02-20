"""add sample salary data

Revision ID: add_salary_data
Revises: d9276dc5649e
Create Date: 2026-02-21

This migration adds sample salary data for employees.
Demonstrates proper way to seed data using Alembic migrations.
"""
from alembic import op
import sqlalchemy as sa
from datetime import date

# revision identifiers, used by Alembic.
revision = 'add_salary_data'
down_revision = 'd9276dc5649e'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add sample salary data for all employees.
    
    Database Design Principles:
    - Each employee can have multiple salary records (One-to-Many relationship)
    - effective_to = NULL means this is the current salary
    - effective_to != NULL means historical salary record
    - Foreign Key employee_id ensures referential integrity
    """
    
    # Create a connection
    conn = op.get_bind()
    
    # Get all employee IDs
    result = conn.execute(sa.text("SELECT id FROM employees"))
    employee_ids = [row[0] for row in result]
    
    # Prepare salary data
    # Using parameterized queries to prevent SQL injection
    for emp_id in employee_ids:
        conn.execute(
            sa.text("""
                INSERT INTO salaries (employee_id, base_salary, effective_from, effective_to)
                VALUES (:emp_id, :salary, :from_date, :to_date)
            """),
            {
                "emp_id": emp_id,
                "salary": 50000000.0,  # 50 million VND
                "from_date": date(2025, 1, 1),
                "to_date": None  # Current salary
            }
        )
    
    print(f"✓ Added salary records for {len(employee_ids)} employees")


def downgrade():
    """
    Remove sample salary data.
    
    This demonstrates database reversibility - important for maintaining
    database integrity during development.
    """
    conn = op.get_bind()
    
    # Delete all salary records with effective_from = 2025-01-01
    conn.execute(
        sa.text("""
            DELETE FROM salaries 
            WHERE effective_from = :from_date
        """),
        {"from_date": date(2025, 1, 1)}
    )
    
    print("✓ Removed sample salary data")
