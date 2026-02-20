# Database Schema và Relationships

## 📚 Kiến Thức Cơ Bản

### 1. Primary Key (Khóa Chính)
- Định danh duy nhất cho mỗi record trong bảng
- Không được NULL, không được trùng
- Thường là `id INTEGER PRIMARY KEY`

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,  -- Auto-increment, unique
    name VARCHAR(100)
);
```

### 2. Foreign Key (Khóa Ngoại)
- Tạo mối quan hệ giữa 2 bảng
- Đảm bảo **Referential Integrity** (toàn vẹn tham chiếu)
- Giá trị phải tồn tại trong bảng được tham chiếu

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    department_id INTEGER,
    
    -- Foreign Key constraint
    FOREIGN KEY (department_id) 
        REFERENCES departments(id)
        ON DELETE SET NULL  -- Khi xóa department, set NULL
);
```

### 3. Relationship Types

#### Many-to-One (N-1)
Nhiều employees thuộc 1 department:
```
employees.department_id → departments.id

employees:
  id=1, name="Thanh", department_id=1  ─┐
  id=2, name="Son",   department_id=1  ─┼→ departments: id=1, name="Engineering"
  id=3, name="Tan",   department_id=1  ─┘
  id=4, name="Lan",   department_id=2  ──→ departments: id=2, name="HR"
```

**SQL Query**:
```sql
-- Lấy danh sách employees với department name
SELECT 
    e.id,
    e.name as employee_name,
    d.name as department_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.id;
```

#### One-to-Many (1-N)
1 employee có nhiều salary records (temporal data):
```
employees.id ← salaries.employee_id

employees: id=1, name="Thanh"
           ↑
           ├─ salaries: id=1, employee_id=1, base=30M, effective_from=2023, effective_to=2024
           ├─ salaries: id=2, employee_id=1, base=40M, effective_from=2024, effective_to=2025
           └─ salaries: id=3, employee_id=1, base=50M, effective_from=2025, effective_to=NULL (current)
```

**SQL Query - Lương Hiện Tại**:
```sql
SELECT 
    e.id,
    e.name,
    s.base_salary as current_salary
FROM employees e
LEFT JOIN salaries s 
    ON s.employee_id = e.id 
    AND s.effective_to IS NULL  -- Chỉ lấy lương hiện tại
;
```

**SQL Query - Lịch Sử Lương**:
```sql
SELECT 
    e.id,
    e.name,
    s.base_salary,
    s.effective_from,
    s.effective_to,
    CASE 
        WHEN s.effective_to IS NULL THEN 'Current'
        ELSE 'Historical'
    END as status
FROM employees e
INNER JOIN salaries s ON s.employee_id = e.id
WHERE e.id = 1
ORDER BY s.effective_from DESC;
```

### 4. ON DELETE Behaviors

#### CASCADE
Xóa parent → tự động xóa children
```sql
FOREIGN KEY (employee_id) 
    REFERENCES employees(id) 
    ON DELETE CASCADE
```
**Use case**: salaries, attendances, leaves
- Xóa employee → xóa toàn bộ lương, chấm công, nghỉ phép

#### SET NULL
Xóa parent → set children's FK = NULL
```sql
FOREIGN KEY (department_id) 
    REFERENCES departments(id) 
    ON DELETE SET NULL
```
**Use case**: employees.department_id
- Xóa department → employees vẫn tồn tại, nhưng department_id = NULL

#### RESTRICT (default)
Không cho xóa parent nếu còn children
```sql
FOREIGN KEY (department_id) 
    REFERENCES departments(id) 
    ON DELETE RESTRICT
```

### 5. Constraints (Ràng Buộc)

#### CHECK Constraint
```sql
CREATE TABLE salaries (
    base_salary NUMERIC(15,2),
    effective_from DATE,
    effective_to DATE,
    
    CHECK (base_salary > 0),  -- Lương phải dương
    CHECK (effective_to IS NULL OR effective_to >= effective_from)  -- Logic validation
);
```

#### UNIQUE Constraint
```sql
CREATE TABLE employees (
    email VARCHAR(100) UNIQUE,  -- Email không được trùng
    employee_code VARCHAR(20) UNIQUE
);
```

## 🎯 Schema Của Dự Án

```
┌─────────────┐         ┌─────────────┐
│ departments │         │  positions  │
│─────────────│         │─────────────│
│ id (PK)     │         │ id (PK)     │
│ name        │         │ title       │
└─────────────┘         └─────────────┘
       ↑                       ↑
       │ 1                     │ 1
       │                       │
       │ N                     │ N
┌─────────────┐         ┌─────────────┐
│  employees  │──── 1:N ─→│  salaries   │
│─────────────│         │─────────────│
│ id (PK)     │         │ id (PK)     │
│ name        │         │ employee_id │ (FK)
│ email       │         │ base_salary │
│ department_id (FK)    │ effective_from
│ position_id (FK)      │ effective_to │ (NULL = current)
└─────────────┘         └─────────────┘
       │ 1
       │
       │ N
┌─────────────┐
│ attendances │
│─────────────│
│ id (PK)     │
│ employee_id │ (FK, CASCADE)
│ date        │
│ status      │
└─────────────┘
```

## 📝 SQL Learning Queries

### Query 1: Employees with Department and Position
```sql
SELECT 
    e.id,
    e.name,
    d.name as department,
    p.title as position
FROM employees e
LEFT JOIN departments d ON e.department_id = d.id
LEFT JOIN positions p ON e.position_id = p.id;
```

### Query 2: Department Statistics
```sql
SELECT 
    d.id,
    d.name as department_name,
    COUNT(e.id) as total_employees,
    AVG(s.base_salary) as avg_salary,
    MIN(s.base_salary) as min_salary,
    MAX(s.base_salary) as max_salary
FROM departments d
LEFT JOIN employees e ON e.department_id = d.id
LEFT JOIN salaries s ON s.employee_id = e.id AND s.effective_to IS NULL
GROUP BY d.id, d.name
ORDER BY total_employees DESC;
```

### Query 3: Salary History
```sql
SELECT 
    e.name,
    s.base_salary,
    s.effective_from,
    COALESCE(s.effective_to::TEXT, 'Present') as effective_to,
    s.base_salary - LAG(s.base_salary) OVER (
        PARTITION BY e.id 
        ORDER BY s.effective_from
    ) as salary_increase
FROM employees e
INNER JOIN salaries s ON s.employee_id = e.id
WHERE e.id = 1
ORDER BY s.effective_from;
```

## 🛠️ Tạo Dữ Liệu Đúng Cách

### Cách 1: Alembic Migration (Recommended)
```bash
# Chạy migration
alembic upgrade head
```

### Cách 2: Qua API Endpoint
```python
# POST /api/v1/salaries
{
  "employee_id": 1,
  "base_salary": 50000000,
  "effective_from": "2025-01-01",
  "effective_to": null
}
```

### ❌ KHÔNG NÊN:
- Chạy script Python trực tiếp insert vào DB
- Bypass ORM và constraints
- Tạo dữ liệu không có trong migration history

### ✅ NÊN:
- Dùng Alembic migration cho seed data
- Hoặc tạo qua API với validation
- Maintain migration history để rollback được
