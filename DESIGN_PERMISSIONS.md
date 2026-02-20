# THIẾT KẾ PHÂN QUYỀN HỆ THỐNG QUẢN LÝ NHÂN VIÊN
===============================================

## 1. CÁC ROLE VÀ QUYỀN HẠN

### 🔵 EMPLOYEE (Nhân viên)
**Attendances (Chấm công):**
- ✅ Check-in/Check-out cho bản thân (MARK_OWN_ATTENDANCE)
- ✅ Xem lịch sử chấm công của mình (READ_OWN_ATTENDANCE)
- ❌ KHÔNG được sửa giờ chấm công (NO UPDATE_ATTENDANCE)
- ❌ KHÔNG được xóa chấm công

**Salaries (Lương):**
- ✅ Xem lương của bản thân (READ_OWN_SALARY)
- ❌ KHÔNG xem lương nhân viên khác
- ❌ KHÔNG tạo/sửa/xóa lương

**Leaves (Nghỉ phép):**
- ✅ Tạo đơn xin nghỉ (REQUEST_OWN_LEAVE)
- ✅ Xem đơn nghỉ của mình (READ_OWN_LEAVE)
- ❌ KHÔNG duyệt đơn

**Employees (Nhân viên):**
- ✅ Xem thông tin cá nhân (READ_OWN_EMPLOYEE_DATA)
- ❌ KHÔNG xem danh sách nhân viên khác

**Departments/Positions:**
- ✅ Xem danh sách (READ_DEPARTMENT, READ_POSITION)
- ❌ KHÔNG tạo/sửa/xóa

---

### 🟢 MANAGER (Quản lý)
**Attendances:**
- ✅ Xem tất cả chấm công (READ_ATTENDANCE)
- ✅ Tạo chấm công cho nhân viên (CREATE_ATTENDANCE)
- ✅ Sửa giờ chấm công (UPDATE_ATTENDANCE) 👈 Khác Employee
- ❌ Không xóa chấm công

**Salaries:**
- ✅ Xem lương tất cả nhân viên (READ_SALARY) 👈 Khác Employee
- ✅ Tạo lương (CREATE_SALARY) 👈 Khác Employee
- ✅ Sửa lương (UPDATE_SALARY) 👈 Khác Employee
- ❌ Không xóa lương

**Leaves:**
- ✅ Xem tất cả đơn nghỉ (READ_LEAVE)
- ✅ Duyệt/Từ chối đơn (APPROVE_LEAVE) 👈 Khác Employee
- ✅ Sửa đơn nghỉ (UPDATE_LEAVE)

**Employees:**
- ✅ Xem danh sách nhân viên (READ_EMPLOYEE)
- ✅ Tạo nhân viên (CREATE_EMPLOYEE)
- ✅ Sửa thông tin nhân viên (UPDATE_EMPLOYEE)
- ❌ Không xóa nhân viên

**Users:**
- ✅ Tạo user (CREATE_USER)
- ✅ Xem user (READ_USER)
- ❌ Không xóa user
- ❌ Không gán role Admin

**Departments/Positions:**
- ✅ Xem (READ)
- ✅ Tạo (CREATE)
- ✅ Sửa (UPDATE)
- ❌ Không xóa

---

### 🔴 ADMIN (Quản trị viên)
**Full permissions cho tất cả:**
- ✅ Users: CREATE, READ, UPDATE, DELETE
- ✅ Employees: CREATE, READ, UPDATE, DELETE
- ✅ Attendances: CREATE, READ, UPDATE, DELETE
- ✅ Salaries: CREATE, READ, UPDATE, DELETE
- ✅ Leaves: CREATE, READ, UPDATE, DELETE, APPROVE
- ✅ Departments: CREATE, READ, UPDATE, DELETE
- ✅ Positions: CREATE, READ, UPDATE, DELETE

---

## 2. ENDPOINTS VÀ PERMISSIONS

### Attendances API
```
GET    /attendances/               - READ_ATTENDANCE (Manager/Admin)
GET    /attendances/my-attendances - READ_OWN_ATTENDANCE (Employee)
POST   /attendances/check-in       - MARK_OWN_ATTENDANCE (Employee)
POST   /attendances/check-out      - MARK_OWN_ATTENDANCE (Employee)
POST   /attendances/               - CREATE_ATTENDANCE (Manager/Admin)
PUT    /attendances/{id}           - UPDATE_ATTENDANCE (Manager/Admin)
DELETE /attendances/{id}           - DELETE_ATTENDANCE (Admin only)
```

### Salaries API
```
GET    /salaries/                  - READ_SALARY (Manager/Admin)
GET    /salaries/my-salary         - READ_OWN_SALARY (Employee)
POST   /salaries/                  - CREATE_SALARY (Manager/Admin)
PUT    /salaries/{id}              - UPDATE_SALARY (Manager/Admin)
DELETE /salaries/{id}              - DELETE_SALARY (Admin only)
```

### Leaves API
```
GET    /leaves/                    - READ_LEAVE (Manager/Admin)
GET    /leaves/my-leaves           - READ_OWN_LEAVE (Employee)
POST   /leaves/                    - REQUEST_OWN_LEAVE (Employee for self)
PUT    /leaves/{id}                - UPDATE_LEAVE (Manager/Admin)
PUT    /leaves/{id}/approve        - APPROVE_LEAVE (Manager/Admin)
PUT    /leaves/{id}/reject         - APPROVE_LEAVE (Manager/Admin)
DELETE /leaves/{id}                - DELETE_LEAVE (Admin only)
```

### Employees API
```
GET    /employees/                 - READ_EMPLOYEE (Manager/Admin)
GET    /employees/me               - READ_OWN_EMPLOYEE_DATA (Employee)
POST   /employees/                 - CREATE_EMPLOYEE (Manager/Admin)
PUT    /employees/{id}             - UPDATE_EMPLOYEE (Manager/Admin)
DELETE /employees/{id}             - DELETE_EMPLOYEE (Admin only)
```

---

## 3. FRONTEND UI THEO ROLE

### AttendancesPage
**Employee:**
- ✅ Button "Check In", "Check Out"
- ✅ Datagrid xem lịch sử chấm công của mình (read-only)
- ❌ HIDE: Edit, Delete buttons

**Manager/Admin:**
- ✅ Button "Add Attendance" (tạo chấm công cho nhân viên)
- ✅ Button "Edit" (sửa giờ chấm công)
- ✅ Button "Delete" (Admin only)
- ✅ Datagrid với tất cả nhân viên

### SalariesPage
**Employee:**
- ✅ Hiển thị CHÍNH lương của mình
- ❌ HIDE: Add, Edit, Delete buttons
- ❌ Không thấy dropdown chọn nhân viên

**Manager/Admin:**
- ✅ Button "Add Salary"
- ✅ Button "Edit"
- ✅ Button "Delete" (Admin only)
- ✅ Datagrid với tất cả nhân viên
- ✅ Filter by Employee

### LeavesPage
**Employee:**
- ✅ Button "Request Leave" (tạo đơn xin nghỉ)
- ✅ Datagrid xem đơn của mình (read-only)
- ❌ HIDE: Approve, Reject buttons

**Manager/Admin:**
- ✅ Button "Approve", "Reject"
- ✅ Datagrid với tất cả đơn nghỉ
- ✅ Filter by status (Pending, Approved, Rejected)

### EmployeesPage
**Employee:**
- ❌ HIDE: Không thấy page này (Navigation menu hidden)
- ✅ Chỉ xem thông tin cá nhân qua "My Profile"

**Manager/Admin:**
- ✅ Button "Add Employee"
- ✅ Button "Edit"
- ✅ Button "Delete" (Admin only)
- ✅ Full datagrid

### DepartmentsPage & PositionsPage
**Employee:**
- ✅ Xem danh sách (read-only)
- ❌ HIDE: Add, Edit, Delete buttons

**Manager:**
- ✅ Button "Add", "Edit"
- ❌ HIDE: Delete button

**Admin:**
- ✅ Full CRUD buttons

### UsersPage
**Employee:**
- ❌ HIDE: Không thấy page này

**Manager:**
- ✅ Button "Add User" (chỉ tạo Employee/Manager)
- ✅ Xem danh sách users
- ❌ HIDE: Delete button

**Admin:**
- ✅ Full CRUD buttons
- ✅ Gán role Admin

---

## 4. DATABASE SCHEMA (SQLite)

**users**
- id, username, hashed_password, role, is_active, employee_id

**employees**
- id, employee_code, full_name, email, phone, department_id, position_id, hire_date

**departments**
- id, name, description

**positions**
- id, title, description

**salaries**
- id, employee_id, base_salary, effective_from, effective_to

**attendances**
- id, employee_id, date, check_in_time, check_out_time, status

**leaves**
- id, employee_id, start_date, end_date, leave_type, reason, status, approved_by

---

## 5. KEY BUSINESS RULES

1. **Attendance:**
   - Employee chỉ check-in/out cho CHÍNH MÌNH
   - Không được sửa giờ đã chấm
   - Manager/Admin có thể sửa giờ cho bất kỳ ai

2. **Salary:**
   - Employee chỉ xem lương CỦA MÌNH
   - Manager/Admin tạo và quản lý lương cho tất cả

3. **Leave:**
   - Employee tạo đơn xin nghỉ
   - Manager/Admin duyệt đơn
   - Đơn đã duyệt không thể xóa (chỉ Admin)

4. **Data Isolation:**
   - Employee KHÔNG thấy data của người khác
   - Manager/Admin thấy tất cả

5. **Ownership Check:**
   - Backend verify employee_id trùng với current_user.employee_id
   - Frontend disable buttons theo role
