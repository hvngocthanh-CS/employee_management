# GIẢI THÍCH: TẠI SAO XÓA SALARY KHỎI EMPLOYEE FORM?

## ❌ VẤN ĐỀ TRƯỚC KHAI

### User nói đúng:
> "lương bên salary đổi còn bên employee không đổi vậy"

**Vấn đề**: Khi có 2 nơi quản lý lương (Employee form + Salaries table), dữ liệu bị **mất đồng bộ**:

```
Employee Form (Frontend)          Database
─────────────────────              ─────────────────────
User tạo employee                  employees
  salary: 30M VND ──────────X──►     NO salary column ❌
                                   
                                   salaries table
                                     NO record ❌
                                   
→ RESULT: Dữ liệu không khớp!
```

## ✅ THIẾT KẾ MỚI (ĐÚNG SQL RELATIONSHIP)

### Database Schema (SINGLE SOURCE OF TRUTH):

```sql
-- Bảng employees: KHÔNG CÓ salary column
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    position_id INTEGER REFERENCES positions(id) ON DELETE SET NULL,
    hire_date DATE
    -- ✅ NO salary column here!
);

-- Bảng salaries: NƠI DUY NHẤT lưu lương
CREATE TABLE salaries (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    base_salary NUMERIC(15,2) NOT NULL CHECK (base_salary > 0),
    effective_from DATE NOT NULL,
    effective_to DATE,  -- NULL = lương hiện tại
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign Key Constraint
    CONSTRAINT fk_salaries_employee 
        FOREIGN KEY (employee_id) 
        REFERENCES employees(id) 
        ON DELETE CASCADE
);
```

### Relationship (One-to-Many):

```
┌──────────────┐         ┌──────────────┐
│  employees   │1       *│   salaries   │
│              ├─────────┤              │
│  id (PK)     │         │  employee_id │
│  full_name   │         │  (FK)        │
│  email       │         │              │
│  department  │         │  base_salary │
│  position    │         │  effective_  │
│  hire_date   │         │    from/to   │
│              │         │              │
│ ❌ NO salary │         │ ✅ All salary│
│    here!     │         │    data here!│
└──────────────┘         └──────────────┘

Giải thích:
- 1 employee có NHIỀU salary records (lịch sử thay đổi lương)
- 1 salary record thuộc về 1 employee duy nhất
- Foreign Key employee_id đảm bảo data integrity
```

## 🔄 WORKFLOW ĐÚNG

### 1. TẠO NHÂN VIÊN MỚI (Employee Form)
```yaml
Frontend: EmployeesPage.xaml
  Fields:
    - First Name ✅
    - Last Name ✅  
    - Email ✅
    - Password ✅
    - Phone ✅
    - Department (FK) ✅
    - Position (FK) ✅
    - Hire Date ✅
    # ❌ NO Salary field!
    
Backend: POST /api/v1/employees
  Request:
    {
      "first_name": "Nguyen Van",
      "last_name": "A",
      "email": "nguyenvana@test.com",
      "password": "password123",
      "department_id": 1,
      "position_id": 2,
      "hire_date": "2026-03-01"
      # ❌ NO "salary" field!
    }
  
  Database:
    INSERT INTO employees (full_name, email, ...) VALUES (...);
    → employee_id = 6
```

### 2. THÊM LƯƠNG CHO NHÂN VIÊN (Salaries Page/API)
```yaml
Frontend: SalariesPage.xaml (tạo sau)
  Fields:
    - Employee (ComboBox - select từ danh sách) ✅
    - Base Salary ✅
    - Effective From ✅
    - Effective To (nullable) ✅
    
Backend: POST /api/v1/salaries
  Request:
    {
      "employee_id": 6,  ← Foreign Key reference
      "base_salary": 30000000.0,
      "effective_from": "2026-03-01",
      "effective_to": null  ← NULL = lương hiện tại
    }
  
  Database:
    INSERT INTO salaries (employee_id, base_salary, effective_from, effective_to)
    VALUES (6, 30000000.0, '2026-03-01', NULL);
    
  Foreign Key Check:
    ✅ employee_id = 6 tồn tại trong employees table
    → Insert thành công
```

### 3. HIỂN THỊ NHÂN VIÊN (DataGrid)
```yaml
Frontend: EmployeesPage DataGrid
  Columns:
    - Name ✅
    - Email ✅
    - Department ✅
    - Position ✅
    - Salary (VND) ✅  ← Binding="{Binding salary}"
    
Backend: GET /api/v1/employees
  SQL Query:
    SELECT 
        e.id,
        e.full_name,
        e.email,
        d.name as department_name,
        p.title as position_title,
        s.base_salary as salary  ← LEFT JOIN với salaries
    FROM employees e
    LEFT JOIN departments d ON d.id = e.department_id
    LEFT JOIN positions p ON p.id = e.position_id
    LEFT JOIN salaries s 
        ON s.employee_id = e.id 
        AND s.effective_to IS NULL  ← Chỉ lấy lương hiện tại
    ORDER BY e.id;
  
  Response:
    {
      "id": 6,
      "full_name": "Nguyen Van A",
      "email": "nguyenvana@test.com",
      "department_name": "IT",
      "position_title": "Software Engineer",
      "salary": 30000000.0  ← Từ salaries table
    }
```

### 4. TĂNG LƯƠNG (Update Salary)
```yaml
Cách 1: Đóng lương cũ + Tạo lương mới (RECOMMENDED)
  
  Step 1: Đóng lương cũ
    PUT /api/v1/salaries/5
    {
      "effective_to": "2026-06-30"  ← Kết thúc lương cũ
    }
    
    Database:
      UPDATE salaries 
      SET effective_to = '2026-06-30' 
      WHERE id = 5;
  
  Step 2: Tạo lương mới
    POST /api/v1/salaries
    {
      "employee_id": 6,
      "base_salary": 35000000.0,  ← Tăng lên 35M
      "effective_from": "2026-07-01",
      "effective_to": null  ← Lương mới
    }
    
    Database:
      INSERT INTO salaries (employee_id, base_salary, effective_from, effective_to)
      VALUES (6, 35000000.0, '2026-07-01', NULL);

Cách 2: Soft delete cũ + Insert mới (Alternative)
  
  UPDATE salaries SET effective_to = NOW() WHERE employee_id = 6 AND effective_to IS NULL;
  INSERT INTO salaries (...) VALUES (...);
```

## 📊 QUERY LƯƠNG (SQL LEARNING)

### Query 1: Lương hiện tại của tất cả employees
```sql
SELECT 
    e.id,
    e.full_name,
    s.base_salary AS current_salary,
    s.effective_from AS salary_start_date
FROM employees e
LEFT JOIN salaries s 
    ON s.employee_id = e.id 
    AND s.effective_to IS NULL  ← Điều kiện quan trọng!
ORDER BY e.id;
```

**Output:**
```
id | full_name      | current_salary | salary_start_date
---|----------------|----------------|------------------
1  | Son Vo         | 50000000.00    | 2025-01-01
2  | Nguyen Van A   | 50000000.00    | 2025-01-01
6  | Le Van C       | 30000000.00    | 2026-03-01
7  | Tran Thi D     | NULL           | NULL             ← Chưa có lương
```

### Query 2: Lịch sử lương của 1 employee
```sql
SELECT 
    s.id,
    s.base_salary,
    s.effective_from,
    s.effective_to,
    CASE 
        WHEN s.effective_to IS NULL THEN 'Current'
        ELSE 'Historical'
    END AS status,
    s.effective_to - s.effective_from AS duration_days
FROM salaries s
WHERE s.employee_id = 6
ORDER BY s.effective_from DESC;
```

**Output:**
```
id | base_salary | effective_from | effective_to | status     | duration_days
---|-------------|----------------|--------------|------------|---------------
8  | 35000000.00 | 2026-07-01     | NULL         | Current    | NULL
7  | 30000000.00 | 2026-03-01     | 2026-06-30   | Historical | 121 days
```

### Query 3: Employees chưa có lương (cần thêm)
```sql
SELECT 
    e.id,
    e.full_name,
    e.email,
    e.hire_date
FROM employees e
LEFT JOIN salaries s 
    ON s.employee_id = e.id 
    AND s.effective_to IS NULL
WHERE s.id IS NULL  ← Không có salary record
ORDER BY e.hire_date DESC;
```

### Query 4: Tổng chi phí lương theo phòng ban
```sql
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
LEFT JOIN salaries s 
    ON s.employee_id = e.id 
    AND s.effective_to IS NULL
GROUP BY d.id, d.name
HAVING SUM(s.base_salary) > 0  ← Chỉ lấy phòng ban có lương
ORDER BY total_salary_budget DESC;
```

## 🎓 KIẾN THỨC SQL ĐÃ HỌC

### 1. Foreign Key (Khóa Ngoại)
```sql
CONSTRAINT fk_salaries_employee 
    FOREIGN KEY (employee_id) 
    REFERENCES employees(id) 
    ON DELETE CASCADE
```

**Ý nghĩa:**
- `employee_id` trong `salaries` PHẢI tồn tại trong `employees.id`
- Không thể insert `employee_id = 999` nếu không có employee có id = 999
- `ON DELETE CASCADE`: Xóa employee → tự động xóa tất cả salaries của employee đó

### 2. Referential Integrity (Toàn Vẹn Tham Chiếu)
```yaml
Try to insert invalid salary:
  INSERT INTO salaries (employee_id, base_salary, ...) 
  VALUES (9999, 50000000, ...);
  
Result:
  ❌ ERROR: violates foreign key constraint
  ❌ Key (employee_id)=(9999) is not present in table "employees"
```

### 3. Temporal Data Pattern (SCD Type 2)
```yaml
effective_to = NULL → Lương hiện tại (current)
effective_to = DATE → Lương cũ (historical)

Ví dụ lịch sử lương:
  2024-01-01 to 2024-12-31: 20M VND (historical)
  2025-01-01 to 2025-12-31: 25M VND (historical)
  2026-01-01 to NULL:       30M VND (current) ← effective_to IS NULL
```

### 4. LEFT JOIN vs INNER JOIN
```sql
-- LEFT JOIN: Lấy TẤT CẢ employees (kể cả không có salary)
SELECT e.*, s.base_salary
FROM employees e
LEFT JOIN salaries s ON s.employee_id = e.id AND s.effective_to IS NULL;

-- INNER JOIN: CHỈ lấy employees CÓ salary
SELECT e.*, s.base_salary
FROM employees e
INNER JOIN salaries s ON s.employee_id = e.id AND s.effective_to IS NULL;
```

## 🚀 NEXT STEPS (TODO)

### 1. Tạo SalariesPage.xaml (Frontend)
```yaml
Features:
  - DataGrid hiển thị tất cả salary records
  - Form thêm salary cho employee
  - Filter theo employee_id
  - Hiển thị salary history (effective_from/to)
  - Button "Set Current Salary" (đóng cũ + tạo mới)
```

### 2. API Endpoints (Backend - đã có)
```yaml
✅ GET /api/v1/salaries
✅ GET /api/v1/salaries/{id}
✅ POST /api/v1/salaries
✅ PUT /api/v1/salaries/{id}
✅ DELETE /api/v1/salaries/{id}
✅ GET /api/v1/salaries/employee/{employee_id}
```

### 3. Business Rules
```yaml
Rules cần implement:
  1. Không được có 2 salary records với effective_to = NULL cho cùng 1 employee
  2. effective_from phải < effective_to (nếu có)
  3. base_salary phải > 0
  4. Không được có gap trong lịch sử lương (optional)
  5. Không được có overlap dates (optional)
```

## 📝 SUMMARY

### ✅ ĐÃ XONG:
1. ✅ Xóa cột `salary` khỏi bảng `employees` (migration)
2. ✅ Xóa field `Salary` khỏi Employee form (XAML + C#)
3. ✅ Backend API lấy salary từ `salaries` table (LEFT JOIN)
4. ✅ DataGrid hiển thị salary từ API response
5. ✅ Foreign Key constraint: `salaries.employee_id → employees.id`

### 🎯 THIẾT KẾ ĐÚNG:
- **Employee Form**: Chỉ quản lý thông tin nhân viên (name, email, department, position, hire_date)
- **Salaries Table**: Quản lý TẤT CẢ dữ liệu lương với lịch sử thay đổi
- **Foreign Key**: Đảm bảo salary.employee_id PHẢI tồn tại trong employees
- **API**: LEFT JOIN để lấy lương hiện tại (effective_to IS NULL)

### 💡 USER ĐÃ HỌC:
1. Foreign Key relationships (One-to-Many)
2. ON DELETE CASCADE behavior
3. Temporal data pattern (effective dates)
4. LEFT JOIN to get current salary
5. Referential integrity constraints
6. Database normalization (tách salary ra bảng riêng)

Giờ thiết kế hoàn toàn logic và có mối quan hệ rõ ràng giữa các bảng! 🎓
