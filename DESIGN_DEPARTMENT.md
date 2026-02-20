# THIẾT KẾ NÂNG CAO CHỨC NĂNG DEPARTMENT
## Employee Management System - Department Feature Design

---

## 📋 MỤC LỤC
1. [Vấn đề hiện tại](#vấn-đề-hiện-tại)
2. [Mục tiêu thiết kế](#mục-tiêu-thiết-kế)
3. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
4. [Các tính năng nâng cao](#các-tính-năng-nâng-cao)
5. [SQL Queries & Learning Points](#sql-queries--learning-points)
6. [API Endpoints mới](#api-endpoints-mới)
7. [Database Schema](#database-schema)
8. [Frontend Design](#frontend-design)
9. [Roadmap Implementation](#roadmap-implementation)

---

## 🔴 VẤN ĐỀ HIỆN TẠI

### Dashboard hiển thị dữ liệu SAI (hardcoded)
```csharp
// DashboardPage.xaml.cs - Lines 67-72
TotalPositionsText.Text = "5";           // ❌ HARDCODED
PendingLeavesText.Text = "2";            // ❌ HARDCODED
PresentTodayText.Text = "45";            // ❌ HARDCODED
ActiveUsersText.Text = "12";             // ❌ HARDCODED
AverageSalaryText.Text = "50,000,000 VND"; // ❌ HARDCODED
LateTodayText.Text = "3";                // ❌ HARDCODED
```

**Vấn đề**: Dashboard không phản ánh dữ liệu thực, gây nhầm lẫn cho user.

### Department feature quá đơn giản
**Hiện tại chỉ có CRUD cơ bản**:
- ✅ GET /departments - List all
- ✅ GET /departments/{id} - Get one
- ✅ POST /departments - Create
- ✅ PUT /departments/{id} - Update
- ✅ DELETE /departments/{id} - Delete

**Vấn đề**: Không có thống kê, báo cáo, phân tích - không đủ để học SQL nâng cao.

---

## 🎯 MỤC TIÊU THIẾT KẾ

### 1. Học SQL & Database Concepts
- **Basic Queries**: SELECT, WHERE, ORDER BY, LIMIT/OFFSET (Pagination)
- **Aggregate Functions**: COUNT(), SUM(), AVG(), MIN(), MAX()
- **GROUP BY & HAVING**: Phân nhóm và filter nhóm
- **Joins**: INNER JOIN, LEFT JOIN với bảng employees
- **Subqueries**: Nested queries trong WHERE/SELECT
- **Window Functions**: ROW_NUMBER(), RANK() (PostgreSQL advanced)
- **Performance**: EXPLAIN ANALYZE, Indexes, Query optimization

### 2. Business Intelligence cho Department
- Thống kê số lượng nhân viên theo department
- Tổng/trung bình lương theo department
- Phân bố nhân viên theo position trong mỗi department
- Department có nhiều nhân viên nhất/ít nhất
- Department với lương cao nhất/thấp nhất
- Growth trend: Số nhân viên mới theo tháng/quý

### 3. Fix Dashboard với dữ liệu thực
- Tạo API endpoint `/api/v1/statistics/dashboard` trả về tất cả metrics
- Frontend gọi API để lấy dữ liệu real-time
- Cache data hợp lý để tránh query quá nặng

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (WPF C#)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ DashboardPage│  │DepartmentsPage│ │ Statistics Page │  │
│  │  (Real Data) │  │  (Enhanced)   │  │   (New)        │  │
│  └──────┬───────┘  └──────┬────────┘  └────────┬────────┘  │
│         │                 │                     │            │
└─────────┼─────────────────┼─────────────────────┼───────────┘
          │                 │                     │
          │  HTTP GET       │  HTTP GET/POST     │  HTTP GET
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (app/api/v1/)                 │  │
│  │  ┌─────────────┐  ┌─────────────┐ ┌──────────────┐ │  │
│  │  │departments.py│  │statistics.py│ │dashboard.py  │ │  │
│  │  │(Enhanced)   │  │   (New)     │ │   (New)      │ │  │
│  │  └─────┬───────┘  └──────┬──────┘ └──────┬───────┘ │  │
│  └────────┼──────────────────┼────────────────┼─────────┘  │
│           ▼                  ▼                ▼             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Business Logic (app/crud/)                  │  │
│  │  ┌─────────────┐  ┌──────────────┐                  │  │
│  │  │department.py│  │ statistics.py │                  │  │
│  │  │(Enhanced)   │  │    (New)     │                  │  │
│  │  └─────┬───────┘  └──────┬───────┘                  │  │
│  └────────┼──────────────────┼──────────────────────────┘  │
│           ▼                  ▼                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               SQLAlchemy ORM                         │  │
│  └────────────────────┬─────────────────────────────────┘  │
└───────────────────────┼───────────────────────────────────┘
                        ▼
           ┌────────────────────────────┐
           │   PostgreSQL Database      │
           │                            │
           │  Tables:                   │
           │  • employees               │
           │  • departments ⭐          │
           │  • positions               │
           │  • salaries                │
           │  • attendances             │
           │  • leaves                  │
           │  • users                   │
           └────────────────────────────┘
```

---

## 🚀 CÁC TÍNH NĂNG NÂNG CAO

### Feature 1: Department Statistics (Thống kê cơ bản)

**API Endpoint**: `GET /api/v1/departments/{id}/statistics`

**Response Example**:
```json
{
  "department_id": 1,
  "department_name": "Engineering",
  "total_employees": 25,
  "employee_breakdown_by_position": [
    {
      "position_id": 1,
      "position_title": "Software Engineer",
      "count": 15
    },
    {
      "position_id": 2,
      "position_title": "Senior Engineer",
      "count": 8
    },
    {
      "position_id": 5,
      "position_title": "Engineering Manager",
      "count": 2
    }
  ],
  "salary_stats": {
    "total_salary_budget": 1250000000,
    "average_salary": 50000000,
    "min_salary": 15000000,
    "max_salary": 80000000
  },
  "newest_employee": {
    "id": 42,
    "name": "Nguyen Van A",
    "hire_date": "2026-02-10"
  },
  "longest_serving_employee": {
    "id": 5,
    "name": "Tran Thi B",
    "hire_date": "2020-01-15",
    "years_of_service": 6.1
  }
}
```

**SQL Learning Points**:
- COUNT() aggregate
- GROUP BY position_id
- LEFT JOIN departments-employees
- LEFT JOIN employees-salaries
- ORDER BY hire_date ASC/DESC
- LIMIT 1 for newest/oldest
- Date arithmetic (CURRENT_DATE - hire_date)

---

### Feature 2: Department Comparison (So sánh các phòng ban)

**API Endpoint**: `GET /api/v1/departments/compare`

**Query Parameters**:
- `department_ids`: comma-separated IDs (e.g., "1,2,3")
- `metrics`: "employees,salary,positions" (default: all)

**Response Example**:
```json
{
  "comparison": [
    {
      "department_id": 1,
      "department_name": "Engineering",
      "total_employees": 25,
      "total_salary_budget": 1250000000,
      "avg_salary": 50000000,
      "unique_positions": 5,
      "rank_by_size": 1,
      "rank_by_salary": 1
    },
    {
      "department_id": 2,
      "department_name": "Sales",
      "total_employees": 20,
      "total_salary_budget": 800000000,
      "avg_salary": 40000000,
      "unique_positions": 4,
      "rank_by_size": 2,
      "rank_by_salary": 2
    }
  ],
  "summary": {
    "largest_department": "Engineering",
    "highest_paid_department": "Engineering",
    "most_diverse_positions": "Engineering"
  }
}
```

**SQL Learning Points**:
- Multiple JOINs (departments → employees → salaries)
- WHERE IN (department_ids)
- GROUP BY department_id
- HAVING clause
- Subqueries cho ranking
- Window functions: ROW_NUMBER() OVER (ORDER BY ...)

---

### Feature 3: Department Growth Analytics (Phân tích tăng trưởng)

**API Endpoint**: `GET /api/v1/departments/{id}/growth`

**Query Parameters**:
- `period`: "monthly" | "quarterly" | "yearly"
- `start_date`: "2024-01-01"
- `end_date`: "2026-02-21"

**Response Example**:
```json
{
  "department_id": 1,
  "department_name": "Engineering",
  "period": "monthly",
  "growth_data": [
    {
      "period": "2025-12",
      "new_hires": 3,
      "resignations": 1,
      "net_change": 2,
      "end_of_period_count": 23
    },
    {
      "period": "2026-01",
      "new_hires": 2,
      "resignations": 0,
      "net_change": 2,
      "end_of_period_count": 25
    }
  ],
  "summary": {
    "total_new_hires": 5,
    "total_resignations": 1,
    "net_growth": 4,
    "growth_rate": "19.0%"
  }
}
```

**SQL Learning Points**:
- DATE_TRUNC() / EXTRACT() functions
- GROUP BY with date functions
- Self-join on employees table
- CASE WHEN for conditional aggregation
- Time series data handling

---

### Feature 4: Department Dashboard API (Fix Dashboard frontend)

**API Endpoint**: `GET /api/v1/statistics/dashboard`

**Response Example**:
```json
{
  "employees": {
    "total": 67,
    "active": 65,
    "on_leave_today": 2,
    "new_this_month": 5
  },
  "departments": {
    "total": 6,
    "largest": {
      "name": "Engineering",
      "employee_count": 25
    },
    "smallest": {
      "name": "Operations",
      "employee_count": 5
    }
  },
  "positions": {
    "total": 10,
    "most_common": {
      "title": "Software Engineer",
      "count": 15
    }
  },
  "attendance_today": {
    "date": "2026-02-21",
    "present": 45,
    "late": 3,
    "absent": 17,
    "on_leave": 2
  },
  "leaves": {
    "pending_requests": 2,
    "approved_this_month": 8
  },
  "salaries": {
    "total_payroll": 3350000000,
    "average_salary": 50000000,
    "highest_paid_department": "Engineering"
  },
  "users": {
    "total": 12,
    "admins": 2,
    "managers": 4,
    "employees": 6,
    "active_sessions": 8
  }
}
```

**SQL Learning Points**:
- Multiple aggregate queries in single response
- COUNT DISTINCT
- JOINs across multiple tables
- Filtering by date (today, this month)
- Nested aggregations
- Query optimization với proper indexing

---

### Feature 5: Department Search & Filtering

**API Endpoint**: `GET /api/v1/departments/search`

**Query Parameters**:
- `name`: Search by department name (ILIKE)
- `min_employees`: Minimum employee count
- `max_employees`: Maximum employee count
- `min_avg_salary`: Minimum average salary
- `max_avg_salary`: Maximum average salary
- `sort_by`: "name" | "employee_count" | "avg_salary"
- `order`: "asc" | "desc"

**SQL Learning Points**:
- ILIKE / LIKE for pattern matching
- Complex WHERE conditions with AND/OR
- Dynamic ORDER BY
- Computed columns in SELECT
- HAVING with aggregates

---

### Feature 6: Department Employee Details with Pagination

**API Endpoint**: `GET /api/v1/departments/{id}/employees`

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Records per page (default: 10)
- `sort_by`: "name" | "hire_date" | "salary"
- `order`: "asc" | "desc"
- `position_id`: Filter by position (optional)

**Response Example**:
```json
{
  "department_id": 1,
  "department_name": "Engineering",
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_records": 25,
    "total_pages": 3
  },
  "employees": [
    {
      "id": 1,
      "name": "Nguyen Van A",
      "email": "a.nguyen@company.com",
      "position": "Software Engineer",
      "hire_date": "2024-03-15",
      "current_salary": 45000000,
      "years_in_department": 1.9
    }
    // ... 9 more records
  ]
}
```

**SQL Learning Points**:
- OFFSET & LIMIT for pagination
- COUNT(*) OVER() window function (total without separate query)
- Dynamic WHERE clauses
- Multiple ORDER BY columns
- JOIN với position và salary tables

---

## 📊 SQL QUERIES & LEARNING POINTS

### Query 1: Department với số lượng nhân viên
```sql
-- Learning: COUNT(*), GROUP BY, LEFT JOIN
SELECT 
  d.id,
  d.name,
  COUNT(e.id) as employee_count
FROM departments d
LEFT JOIN employees e ON e.department_id = d.id
GROUP BY d.id, d.name
ORDER BY employee_count DESC;
```

**Concepts**:
- LEFT JOIN giữ tất cả departments kể cả không có employees
- COUNT(e.id) đếm chỉ employees thực (không NULL)
- GROUP BY cần bao gồm tất cả non-aggregate columns

---

### Query 2: Department salary statistics
```sql
-- Learning: Multiple aggregates, COALESCE, formatted output
SELECT 
  d.id,
  d.name,
  COUNT(DISTINCT e.id) as employee_count,
  COALESCE(SUM(s.base_salary), 0) as total_salary,
  COALESCE(ROUND(AVG(s.base_salary), 0), 0) as avg_salary,
  COALESCE(MIN(s.base_salary), 0) as min_salary,
  COALESCE(MAX(s.base_salary), 0) as max_salary
FROM departments d
LEFT JOIN employees e ON e.department_id = d.id
LEFT JOIN salaries s ON s.employee_id = e.id
  AND s.effective_to IS NULL  -- Chỉ lấy salary hiện tại
GROUP BY d.id, d.name
ORDER BY total_salary DESC;
```

**Concepts**:
- Multiple LEFT JOINs
- COUNT DISTINCT tránh duplicate do JOIN
- COALESCE xử lý NULL values
- ROUND() làm tròn số
- AND condition trong JOIN clause (salary hiện tại)

---

### Query 3: Department ranking với Window Functions
```sql
-- Learning: Window Functions, RANK(), ROW_NUMBER()
WITH DepartmentStats AS (
  SELECT 
    d.id,
    d.name,
    COUNT(e.id) as employee_count,
    COALESCE(AVG(s.base_salary), 0) as avg_salary
  FROM departments d
  LEFT JOIN employees e ON e.department_id = d.id
  LEFT JOIN salaries s ON s.employee_id = e.id 
    AND s.effective_to IS NULL
  GROUP BY d.id, d.name
)
SELECT 
  id,
  name,
  employee_count,
  avg_salary,
  ROW_NUMBER() OVER (ORDER BY employee_count DESC) as size_rank,
  ROW_NUMBER() OVER (ORDER BY avg_salary DESC) as salary_rank,
  PERCENT_RANK() OVER (ORDER BY employee_count) as size_percentile
FROM DepartmentStats
ORDER BY employee_count DESC;
```

**Concepts**:
- Common Table Expression (CTE) với WITH
- Window Functions không cần GROUP BY
- ROW_NUMBER() vs RANK() vs DENSE_RANK()
- PERCENT_RANK() cho percentile
- Multiple OVER clauses với different ORDER BY

---

### Query 4: Department growth by month
```sql
-- Learning: DATE functions, Time Series, CASE WHEN
SELECT 
  d.id,
  d.name,
  DATE_TRUNC('month', e.hire_date) as month,
  COUNT(*) as new_hires,
  SUM(COUNT(*)) OVER (
    PARTITION BY d.id 
    ORDER BY DATE_TRUNC('month', e.hire_date)
  ) as cumulative_hires
FROM departments d
INNER JOIN employees e ON e.department_id = d.id
WHERE e.hire_date >= '2024-01-01'
GROUP BY d.id, d.name, DATE_TRUNC('month', e.hire_date)
ORDER BY d.id, month;
```

**Concepts**:
- DATE_TRUNC() làm tròn date về đầu tháng
- PARTITION BY trong window function
- Cumulative sum với SUM() OVER
- WHERE filter trước khi aggregate
- Time series data structure

---

### Query 5: Top N employees by salary in each department
```sql
-- Learning: Subquery, WHERE IN, TOP N per group
SELECT 
  d.name as department_name,
  e.name as employee_name,
  e.employee_code,
  s.base_salary,
  RANK() OVER (
    PARTITION BY d.id 
    ORDER BY s.base_salary DESC
  ) as salary_rank_in_dept
FROM employees e
INNER JOIN departments d ON e.department_id = d.id
INNER JOIN salaries s ON s.employee_id = e.id
  AND s.effective_to IS NULL
WHERE d.id IN (1, 2, 3)  -- Specific departments
QUALIFY salary_rank_in_dept <= 3;  -- PostgreSQL 13+

-- Alternative for older PostgreSQL:
-- Wrap in subquery and WHERE rank <= 3
```

**Concepts**:
- RANK() với PARTITION BY cho ranking per group
- QUALIFY clause (PostgreSQL 13+) filter window function results
- Alternative: Subquery với WHERE
- Top N per category pattern

---

### Query 6: Department comparison với subqueries
```sql
-- Learning: Scalar subqueries trong SELECT
SELECT 
  d.id,
  d.name,
  (
    SELECT COUNT(*) 
    FROM employees e 
    WHERE e.department_id = d.id
  ) as employee_count,
  (
    SELECT COALESCE(AVG(s.base_salary), 0)
    FROM employees e
    INNER JOIN salaries s ON s.employee_id = e.id
    WHERE e.department_id = d.id
      AND s.effective_to IS NULL
  ) as avg_salary,
  (
    SELECT COUNT(DISTINCT e.position_id)
    FROM employees e
    WHERE e.department_id = d.id
  ) as position_diversity
FROM departments d
ORDER BY employee_count DESC;
```

**Concepts**:
- Scalar subquery (returns single value) trong SELECT
- Correlated subquery (references outer query)
- Alternative to JOINs when need separate aggregations
- Performance: May be slower than JOIN approach

---

### Query 7: Department performance EXPLAIN ANALYZE
```sql
-- Learning: Query optimization, EXPLAIN
EXPLAIN ANALYZE
SELECT 
  d.id,
  d.name,
  COUNT(e.id) as employee_count
FROM departments d
LEFT JOIN employees e ON e.department_id = d.id
GROUP BY d.id, d.name;
```

**Output Example**:
```
HashAggregate  (cost=45.50..47.50 rows=100 width=52) (actual time=2.345..2.567 rows=6 loops=1)
  Group Key: d.id
  ->  Hash Left Join  (cost=12.00..42.00 rows=700 width=44) (actual time=0.234..1.890 rows=67 loops=1)
        Hash Cond: (d.id = e.department_id)
        ->  Seq Scan on departments d  (cost=0.00..1.06 rows=6 width=40) (actual time=0.010..0.012 rows=6 loops=1)
        ->  Hash  (cost=8.67..8.67 rows=67 width=4) (actual time=0.210..0.211 rows=67 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 11kB
              ->  Seq Scan on employees e  (cost=0.00..8.67 rows=67 width=4) (actual time=0.005..0.098 rows=67 loops=1)
Planning Time: 0.456 ms
Execution Time: 2.789 ms
```

**Concepts**:
- EXPLAIN ANALYZE shows actual execution plan
- Seq Scan vs Index Scan
- Hash Join vs Nested Loop
- Cost estimation vs actual time
- Memory usage
- Rows estimates

---

### Query 8: Create Indexes for Performance
```sql
-- Learning: Indexes, Performance tuning
-- Implicit index tạo tự động trên PRIMARY KEY (departments.id)

-- Index for foreign key lookup (tăng tốc JOIN)
CREATE INDEX idx_employees_department_id 
ON employees(department_id);

-- Index for salary queries
CREATE INDEX idx_salaries_employee_effective 
ON salaries(employee_id, effective_to);

-- Composite index for filtering and sorting
CREATE INDEX idx_employees_dept_hire 
ON employees(department_id, hire_date DESC);

-- Analyze impact
EXPLAIN ANALYZE
SELECT * FROM employees WHERE department_id = 1;
-- Should show "Index Scan" instead of "Seq Scan"
```

**Concepts**:
- B-tree indexes (default)
- Composite indexes (multiple columns)
- Index scan vs Sequential scan
- When to use indexes (foreign keys, WHERE, JOIN, ORDER BY)
- Index overhead on INSERT/UPDATE

---

## 🔌 API ENDPOINTS MỚI

### Summary Table

| Method | Endpoint | Description | SQL Concepts |
|--------|----------|-------------|--------------|
| GET | `/api/v1/departments/{id}/statistics` | Thống kê department | COUNT, GROUP BY, JOIN |
| GET | `/api/v1/departments/compare` | So sánh departments | Multiple aggregates, Window functions |
| GET | `/api/v1/departments/{id}/growth` | Phân tích tăng trưởng | DATE functions, Time series |
| GET | `/api/v1/departments/search` | Tìm kiếm nâng cao | LIKE, Complex WHERE, ORDER BY |
| GET | `/api/v1/departments/{id}/employees` | Danh sách employees có phân trang | OFFSET/LIMIT, Pagination |
| GET | `/api/v1/statistics/dashboard` | Dashboard metrics | Multiple JOINs, Aggregations |
| GET | `/api/v1/departments/{id}/salary-distribution` | Phân bố lương | CASE WHEN, Binning |
| GET | `/api/v1/departments/top-performers` | Top departments by metrics | Ranking, LIMIT |

---

## 💾 DATABASE SCHEMA

### Current Schema
```sql
-- departments table (hiện tại)
CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL
);

-- employees table (liên quan)
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  employee_code VARCHAR(20) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  phone VARCHAR(20),
  hire_date DATE NOT NULL,
  department_id INTEGER REFERENCES departments(id),  -- FOREIGN KEY
  position_id INTEGER REFERENCES positions(id),      -- FOREIGN KEY
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- salaries table (liên quan)
CREATE TABLE salaries (
  id SERIAL PRIMARY KEY,
  employee_id INTEGER REFERENCES employees(id),
  base_salary NUMERIC(15, 2) NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE,  -- NULL = current salary
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes cần thêm (Performance)
```sql
-- Tăng tốc department statistics queries
CREATE INDEX idx_employees_department_id ON employees(department_id);
CREATE INDEX idx_salaries_employee_effective ON salaries(employee_id, effective_to);
CREATE INDEX idx_employees_hire_date ON employees(hire_date);

-- Tăng tốc search queries
CREATE INDEX idx_departments_name_trgm ON departments USING gin(name gin_trgm_ops);  -- Full-text search
```

### Potential Enhancements (Optional)
```sql
-- Thêm metadata cho departments (optional)
ALTER TABLE departments 
  ADD COLUMN description TEXT,
  ADD COLUMN manager_id INTEGER REFERENCES employees(id),
  ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Audit log cho changes (optional)
CREATE TABLE department_audit_log (
  id SERIAL PRIMARY KEY,
  department_id INTEGER REFERENCES departments(id),
  action VARCHAR(20),  -- 'CREATE', 'UPDATE', 'DELETE'
  changed_by INTEGER REFERENCES users(id),
  old_values JSONB,
  new_values JSONB,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎨 FRONTEND DESIGN

### Enhanced DepartmentsPage.xaml Layout
```
┌─────────────────────────────────────────────────────────┐
│  Departments Management                      [+ Add]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Search: [________________] 🔍                          │
│  Filter: [Min Employees ▼] [Max Employees ▼]           │
│  Sort:   [By Name ▼] [Ascending ▼]                     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ID │ Name        │ Employees │ Avg Salary │ ... │  │
│  ├────┼─────────────┼───────────┼────────────┼─────┤  │
│  │ 1  │ Engineering │    25     │ 50,000,000 │[📊]│  │
│  │ 2  │ HR          │    12     │ 35,000,000 │[📊]│  │
│  │ 3  │ Sales       │    20     │ 40,000,000 │[📊]│  │
│  │ 4  │ Marketing   │    8      │ 38,000,000 │[📊]│  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  < Previous  Page 1 of 3  Next >                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### New Statistics Dialog (Click 📊 button)
```
┌─────────────────────────────────────────────────────────┐
│  Engineering Department - Statistics         [✖ Close] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 OVERVIEW                                            │
│  ─────────────────────────────────────────────────────  │
│  Total Employees:        25                             │
│  Active Employees:       24                             │
│  On Leave:               1                              │
│                                                         │
│  💰 SALARY STATISTICS                                   │
│  ─────────────────────────────────────────────────────  │
│  Total Budget:           1,250,000,000 VND              │
│  Average:                50,000,000 VND                 │
│  Min:                    15,000,000 VND                 │
│  Max:                    80,000,000 VND                 │
│                                                         │
│  👥 POSITION BREAKDOWN                                  │
│  ─────────────────────────────────────────────────────  │
│  Software Engineer:      15 employees (60%)             │
│  Senior Engineer:        8 employees (32%)              │
│  Engineering Manager:    2 employees (8%)               │
│                                                         │
│  📈 GROWTH (Last 6 months)                              │
│  ─────────────────────────────────────────────────────  │
│  [Chart: Employee count over time]                      │
│                                                         │
│  [View Detailed Report] [Export to Excel]               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Fixed DashboardPage.xaml (Real Data)
```
┌─────────────────────────────────────────────────────────┐
│  Dashboard                                    🔄 Refresh│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ │
│  │    67     │ │     6     │ │    10     │ │   2    │ │
│  │ Employees │ │ Departments│ │ Positions │ │ Leaves │ │
│  └───────────┘ └───────────┘ └───────────┘ └────────┘ │
│                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ │
│  │    45     │ │     12    │ │50,000,000 │ │   3    │ │
│  │  Present  │ │   Users   │ │ Avg Salary│ │  Late  │ │
│  └───────────┘ └───────────┘ └───────────┘ └────────┘ │
│                                                         │
│  📊 LARGEST DEPARTMENTS                                 │
│  1. Engineering (25 employees)                          │
│  2. Sales (20 employees)                                │
│  3. HR (12 employees)                                   │
│                                                         │
│  💰 HIGHEST PAID DEPARTMENTS                            │
│  1. Engineering (avg: 50M VND)                          │
│  2. Sales (avg: 40M VND)                                │
│  3. Marketing (avg: 38M VND)                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🗺️ ROADMAP IMPLEMENTATION

### Phase 1: Fix Dashboard (Priority: HIGH ⚠️)
**Thời gian**: 1-2 ngày

#### Backend Tasks:
1. ✅ Tạo file `app/api/v1/statistics.py` - Dashboard API endpoint
2. ✅ Tạo file `app/crud/statistics.py` - Dashboard queries
3. ✅ Implement `GET /api/v1/statistics/dashboard` endpoint
4. ✅ Test với Postman/curl

**SQL Queries cần viết**:
```python
# statistics.py
def get_dashboard_metrics(db: Session) -> dict:
    # Query 1: Count employees
    total_employees = db.query(func.count(Employee.id)).scalar()
    
    # Query 2: Count departments
    total_departments = db.query(func.count(Department.id)).scalar()
    
    # Query 3: Count positions
    total_positions = db.query(func.count(Position.id)).scalar()
    
    # Query 4: Pending leaves
    pending_leaves = db.query(func.count(Leave.id))\
        .filter(Leave.status == 'pending').scalar()
    
    # Query 5: Attendance today
    today = date.today()
    present_today = db.query(func.count(Attendance.id))\
        .filter(
            Attendance.attendance_date == today,
            Attendance.status == 'present'
        ).scalar()
    
    # ... etc
```

#### Frontend Tasks:
1. ✅ Update `DashboardPage.xaml.cs`
2. ✅ Thêm method `LoadRealDashboardData()`
3. ✅ Gọi API `/api/v1/statistics/dashboard`
4. ✅ Bind data to TextBlocks
5. ✅ Add error handling

---

### Phase 2: Department Basic Statistics (Priority: HIGH)
**Thời gian**: 2-3 ngày

#### Backend Tasks:
1. ✅ Enhance `app/crud/department.py`:
   - `get_department_statistics(db, department_id)`
   - `get_departments_with_employee_count(db)`
2. ✅ Update `app/api/v1/departments.py`:
   - `GET /api/v1/departments/{id}/statistics`
3. ✅ Create response schemas in `app/schemas/department.py`

**SQL Learning Focus**:
- COUNT() with GROUP BY
- LEFT JOIN departments → employees
- Aggregate functions: SUM, AVG, MIN, MAX

#### Frontend Tasks:
1. ✅ Update `DepartmentsPage.xaml` - Add Statistics button
2. ✅ Create `DepartmentStatisticsDialog.xaml`
3. ✅ Implement data binding

---

### Phase 3: Department Comparison (Priority: MEDIUM)
**Thời gian**: 2-3 ngày

#### Backend Tasks:
1. ✅ Add `app/crud/department.py`:
   - `compare_departments(db, department_ids)`
2. ✅ Add `app/api/v1/departments.py`:
   - `GET /api/v1/departments/compare?ids=1,2,3`

**SQL Learning Focus**:
- Window Functions: ROW_NUMBER(), RANK()
- PARTITION BY
- Multiple aggregations in single query

#### Frontend Tasks:
1. ✅ Create `DepartmentComparisonPage.xaml`
2. ✅ Multi-select departments
3. ✅ Display comparison table

---

### Phase 4: Department Growth Analytics (Priority: MEDIUM)
**Thời gian**: 3-4 ngày

#### Backend Tasks:
1. ✅ Add `app/crud/department.py`:
   - `get_department_growth(db, department_id, period, start, end)`
2. ✅ Add endpoint:
   - `GET /api/v1/departments/{id}/growth`

**SQL Learning Focus**:
- DATE_TRUNC() / EXTRACT()
- Time series queries
- Window functions with PARTITION BY date
- Cumulative aggregations

#### Frontend Tasks:
1. ✅ Add Growth tab in DepartmentStatisticsDialog
2. ✅ Display line chart (optional: use LiveCharts library)

---

### Phase 5: Advanced Search & Filtering (Priority: LOW)
**Thời gian**: 2 ngày

#### Backend Tasks:
1. ✅ Add `app/crud/department.py`:
   - `search_departments(db, filters, sort, pagination)`
2. ✅ Add endpoint:
   - `GET /api/v1/departments/search`

**SQL Learning Focus**:
- LIKE / ILIKE pattern matching
- Complex WHERE with multiple conditions
- Dynamic ORDER BY
- OFFSET/LIMIT pagination

#### Frontend Tasks:
1. ✅ Add search/filter controls in DepartmentsPage
2. ✅ Implement pagination UI

---

### Phase 6: Performance Optimization (Priority: LOW)
**Thời gian**: 1-2 ngày

**Tasks**:
1. ✅ Create indexes:
   ```sql
   CREATE INDEX idx_employees_department_id ON employees(department_id);
   CREATE INDEX idx_salaries_employee_effective ON salaries(employee_id, effective_to);
   ```
2. ✅ Run EXPLAIN ANALYZE on slow queries
3. ✅ Optimize N+1 issues with joinedload()
4. ✅ Add query result caching (Redis optional)

**SQL Learning Focus**:
- EXPLAIN ANALYZE
- Query execution plans
- Index usage
- Query optimization strategies

---

## 📚 LEARNING RESOURCES

### SQL Books & Tutorials
1. **Book**: "PostgreSQL: Up and Running" by Regina O. Obe
2. **Tutorial**: SQLBolt (https://sqlbolt.com/)
3. **Interactive**: Mode Analytics SQL Tutorial
4. **Advanced**: Use The Index, Luke (https://use-the-index-luke.com/)

### SQLAlchemy ORM
1. Official Docs: https://docs.sqlalchemy.org/
2. Focus on:
   - Query API
   - Relationship loading strategies
   - func module for SQL functions
   - Expression language

### Practice Exercises
After implementing each phase:
1. Write the raw SQL query first
2. Translate to SQLAlchemy ORM
3. Compare EXPLAIN plans
4. Optimize if needed
5. Document learnings

---

## ✅ SUCCESS CRITERIA

### Dashboard Fixed
- ✅ All 8 metrics show real data from database
- ✅ No hardcoded values
- ✅ Data refreshes on page load
- ✅ Error handling for API failures

### Department Feature Enhanced
- ✅ Can view detailed statistics for each department
- ✅ Can compare multiple departments
- ✅ Can see growth trends over time
- ✅ Can search and filter departments
- ✅ Pagination works properly

### SQL Learning Goals
- ✅ Understand and write 10+ different query patterns
- ✅ Can explain EXPLAIN ANALYZE output
- ✅ Know when to use indexes
- ✅ Comfortable with JOINs, aggregates, window functions
- ✅ Can optimize slow queries

---

## 🎯 NEXT STEPS

1. **Review this design** - Confirm requirements
2. **Fix Dashboard first** (Phase 1) - High priority bug
3. **Implement Phase 2** - Department statistics
4. **Test with real data** - Add more employees/departments if needed
5. **Iterate** - Add more features based on learning goals

---

**Created**: 2026-02-21  
**Last Updated**: 2026-02-21  
**Status**: 📝 DESIGN PHASE - Awaiting approval to implement
