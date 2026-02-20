# TẠI SAO XÓA `employees.salary`? - GIẢI THÍCH THIẾT KẾ DATABASE

## ❌ VẤN ĐỀ TRƯỚC KHAI (SAI THIẾT KẾ)

### Database có 2 nơi lưu lương:
```sql
-- Bảng employees (cũ)
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    salary DECIMAL(10, 2),  -- ❌ Cột này SAI THIẾT KẾ
    ...
);

-- Bảng salaries (đúng)
CREATE TABLE salaries (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    base_salary NUMERIC(15, 2),
    effective_from DATE,
    effective_to DATE,  -- NULL = lương hiện tại
    ...
);
```

### Tại sao sai?
1. **Dữ liệu trùng lặp (Data Duplication)**: Cùng 1 thông tin lương nhưng lưu 2 nơi
2. **Không có nguồn dữ liệu chính (No Single Source of Truth)**: `employees.salary` khác `salaries.base_salary` → không biết cái nào đúng?
3. **Không tracking được lịch sử**: Cột `employees.salary` chỉ lưu 1 giá trị, không biết lương cũ như thế nào
4. **Vi phạm Database Normalization**: Thông tin lương nên tách riêng vì có tính temporal (thay đổi theo thời gian)

## ✅ THIẾT KẾ ĐÚNG (SAU KHI SỬA)

### Chỉ còn 1 nơi lưu lương - `salaries` table:
```sql
-- Bảng employees (đã xóa cột salary)
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    hire_date DATE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    position_id INTEGER REFERENCES positions(id) ON DELETE SET NULL
    -- ✅ KHÔNG CÒN cột salary
);

-- Bảng salaries (SINGLE SOURCE OF TRUTH)
CREATE TABLE salaries (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    base_salary NUMERIC(15, 2) CHECK (base_salary > 0),
    effective_from DATE NOT NULL,
    effective_to DATE,  -- NULL = lương hiện tại
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- Indexes for performance
CREATE INDEX idx_salary_employee ON salaries(employee_id);
CREATE INDEX idx_salary_effective_from ON salaries(effective_from);
CREATE INDEX idx_salary_effective_to ON salaries(effective_to);
CREATE INDEX idx_salary_employee_date ON salaries(employee_id, effective_from, effective_to);
```

## 🔑 RELATIONSHIP (MỐI QUAN HỆ)

### 1. Foreign Key Constraint
```sql
-- employee_id trong salaries trỏ đến id trong employees
-- ON DELETE CASCADE: Xóa employee → tự động xóa tất cả lương của employee đó
salaries.employee_id → employees.id (CASCADE)
```

### 2. Relationship Type: ONE-TO-MANY
```
┌──────────────┐         ┌──────────────┐
│  employees   │1       *│   salaries   │
│              ├─────────┤              │
│  id (PK)     │         │  employee_id │
│  full_name   │         │  base_salary │
│  email       │         │  effective_  │
│  hire_date   │         │    from/to   │
└──────────────┘         └──────────────┘

Giải thích:
- 1 employee có NHIỀU salary records (lịch sử lương)
- 1 salary record thuộc về 1 employee duy nhất
```

### 3. SQLAlchemy ORM Relationship
```python
# app/models/employee.py
class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    # ... các fields khác
    
    # Relationship: 1 employee → nhiều salaries
    salaries = relationship(
        "Salary", 
        back_populates="employee",
        cascade="all, delete-orphan"  # Xóa employee → xóa salaries
    )
    
    # Property để lấy lương hiện tại
    @property
    def current_salary(self):
        """Get current salary (where effective_to IS NULL)"""
        current = [s for s in self.salaries if s.effective_to is None]
        return current[0].base_salary if current else None

# app/models/salary.py
class Salary(Base):
    __tablename__ = "salaries"
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(
        Integer, 
        ForeignKey("employees.id", ondelete="CASCADE"),  # ← Foreign Key
        nullable=False
    )
    base_salary = Column(Numeric(15, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)  # NULL = current
    
    # Relationship: 1 salary → 1 employee
    employee = relationship("Employee", back_populates="salaries")
```

## 📊 SQL QUERIES (HỌC SQL)

### Query 1: Lấy nhân viên với lương hiện tại
```sql
-- Dùng LEFT JOIN với điều kiện effective_to IS NULL
SELECT 
    e.id,
    e.full_name,
    e.email,
    e.hire_date,
    s.base_salary AS current_salary,
    s.effective_from AS salary_start_date
FROM employees e
LEFT JOIN salaries s ON s.employee_id = e.id 
    AND s.effective_to IS NULL  -- ← Chỉ lấy lương hiện tại
ORDER BY e.id;
```

**Output:**
```
id | full_name      | email                | current_salary | salary_start_date
---|----------------|----------------------|----------------|------------------
1  | Son Vo         | son.vo@example.com   | 50000000.00    | 2025-01-01
2  | Nguyen Van A   | nguyenvana@test.com  | 50000000.00    | 2025-01-01
3  | Tran Thi B     | tranthib@test.com    | 50000000.00    | 2025-01-01
```

### Query 2: Lịch sử lương của 1 nhân viên
```sql
-- Lấy TẤT CẢ lương (cũ + hiện tại) của employee có id = 1
SELECT 
    s.id,
    s.base_salary,
    s.effective_from,
    s.effective_to,
    CASE 
        WHEN s.effective_to IS NULL THEN 'Current'
        ELSE 'Historical'
    END AS status
FROM salaries s
WHERE s.employee_id = 1
ORDER BY s.effective_from DESC;
```

**Output:**
```
id | base_salary | effective_from | effective_to | status
---|-------------|----------------|--------------|----------
5  | 50000000.00 | 2025-01-01     | NULL         | Current
2  | 20000000.00 | 2024-09-15     | 2024-12-31   | Historical
```

### Query 3: Tổng lương hiện tại theo phòng ban
```sql
-- GROUP BY với JOIN nhiều bảng
SELECT 
    d.id,
    d.name AS department_name,
    COUNT(e.id) AS total_employees,
    SUM(s.base_salary) AS total_salary_budget,
    AVG(s.base_salary) AS average_salary,
    MIN(s.base_salary) AS min_salary,
    MAX(s.base_salary) AS max_salary
FROM departments d
INNER JOIN employees e ON e.department_id = d.id
LEFT JOIN salaries s ON s.employee_id = e.id AND s.effective_to IS NULL
GROUP BY d.id, d.name
ORDER BY total_salary_budget DESC;
```

**Output:**
```
id | department_name | total_employees | total_salary_budget | average_salary | min_salary | max_salary
---|-----------------|-----------------|---------------------|----------------|------------|------------
1  | IT              | 3               | 150000000.00        | 50000000.00    | 50000000   | 50000000
2  | HR              | 2               | 100000000.00        | 50000000.00    | 50000000   | 50000000
```

### Query 4: So sánh lương cũ và mới
```sql
-- Dùng Window Function (LAG) để lấy lương trước đó
SELECT 
    e.full_name,
    s.base_salary AS current_salary,
    LAG(s.base_salary) OVER (
        PARTITION BY s.employee_id 
        ORDER BY s.effective_from
    ) AS previous_salary,
    s.base_salary - LAG(s.base_salary) OVER (
        PARTITION BY s.employee_id 
        ORDER BY s.effective_from
    ) AS salary_increase
FROM employees e
INNER JOIN salaries s ON s.employee_id = e.id
ORDER BY e.id, s.effective_from;
```

## 🔄 CRUD OPERATIONS

### Tạo nhân viên mới (KHÔNG có salary)
```python
# POST /api/v1/employees
{
    "full_name": "Le Van C",
    "email": "levanc@test.com",
    "password": "password123",
    "department_id": 1,
    "position_id": 2,
    "hire_date": "2026-03-01"
    # ✅ KHÔNG CÓ "salary" field nữa!
}
```

### Thêm lương cho nhân viên
```python
# POST /api/v1/salaries
{
    "employee_id": 6,
    "base_salary": 30000000.0,
    "effective_from": "2026-03-01",
    "effective_to": null  # NULL = lương hiện tại
}
```

### Cập nhật lương (tạo record mới)
```python
# 1. Đóng lương cũ (set effective_to)
# PUT /api/v1/salaries/5
{
    "effective_to": "2026-06-30"  # Kết thúc lương cũ
}

# 2. Tạo lương mới
# POST /api/v1/salaries
{
    "employee_id": 1,
    "base_salary": 60000000.0,  # Tăng lương
    "effective_from": "2026-07-01",
    "effective_to": null  # Lương mới
}
```

## 🎓 KIẾN THỨC SQL ĐÃ ÁP DỤNG

### 1. Database Normalization (Chuẩn hóa dữ liệu)
- **1NF (First Normal Form)**: Mỗi cột chỉ chứa 1 giá trị atomic
- **2NF (Second Normal Form)**: Không có partial dependency
- **3NF (Third Normal Form)**: Không có transitive dependency

→ Salary phụ thuộc vào employee → tách ra bảng riêng

### 2. Foreign Key Constraints
```sql
FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
```
- **PRIMARY KEY**: `employees.id` (khóa chính)
- **FOREIGN KEY**: `salaries.employee_id` (khóa ngoại)
- **ON DELETE CASCADE**: Xóa employee → tự động xóa salaries

### 3. Referential Integrity (Toàn vẹn tham chiếu)
- Không thể thêm `employee_id` không tồn tại vào `salaries`
- Không thể xóa employee nếu còn salaries (trừ khi CASCADE)

### 4. Temporal Data Pattern (Dữ liệu theo thời gian)
- `effective_from`: Ngày bắt đầu hiệu lực
- `effective_to`: Ngày kết thúc (NULL = hiện tại)
- Gọi là **Slowly Changing Dimension Type 2 (SCD Type 2)**

### 5. JOIN Operations
- **LEFT JOIN**: Lấy tất cả employees, kể cả không có salary
- **INNER JOIN**: Chỉ lấy employees có salary
- **Multiple JOINs**: employees → departments, employees → salaries

### 6. Aggregate Functions
- **COUNT()**: Đếm số lượng
- **SUM()**: Tổng lương
- **AVG()**: Trung bình
- **MIN()/MAX()**: Thấp nhất/cao nhất

### 7. Window Functions
- **LAG()**: Lấy giá trị hàng trước đó
- **PARTITION BY**: Chia nhóm theo employee_id

## 🚀 LỢI ÍCH THIẾT KẾ MỚI

1. ✅ **Single Source of Truth**: Chỉ có 1 nơi lưu lương → không nhầm lẫn
2. ✅ **Salary History**: Tracking được lịch sử lương qua các năm
3. ✅ **Data Integrity**: Foreign Key đảm bảo dữ liệu đúng
4. ✅ **Flexible Queries**: Dễ query lương hiện tại, lịch sử, so sánh
5. ✅ **Auditability**: Biết chính xác lương thay đổi khi nào
6. ✅ **Scalability**: Dễ thêm fields mới (bonus, allowance, deduction)

## 📝 NOTES

- Migration đã chạy: `alembic upgrade head` → Đã xóa `employees.salary` column
- Model đã update: `Employee` model không còn field `salary`
- API đã update: `enhance_employee_response()` query từ `salaries` relationship
- Schema đã update: `EmployeeCreate`/`EmployeeUpdate` không còn field `salary`

## ⚠️ MIGRATION COMMANDS

```bash
# Xem lịch sử migrations
alembic history

# Upgrade lên version mới nhất
alembic upgrade head

# Downgrade về version trước (nếu cần rollback)
alembic downgrade -1

# Xem SQL sẽ chạy (không thực thi)
alembic upgrade head --sql
```
