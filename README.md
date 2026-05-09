# Task 4 — Role-Based Access Control, Admin Panel & REST API (Flask)

## Quick Start

```bash
cd flask_task4
pip install -r requirements.txt
python app.py
```

Visit: http://127.0.0.1:5000

**Default Admin credentials:**
- Username: `admin`
- Password: `admin123`

---

## Role Logic

The app has two roles stored in the `users.role` column:

| Role  | Permissions |
|-------|-------------|
| admin | View + Add + Edit + Delete students, view all users |
| user  | View students only |

After login, the role is stored in the Flask session:
```python
session['user']  = user['username']
session['role']  = user['role']
```

A custom decorator `@admin_required` protects admin-only routes. Any non-admin hitting an admin URL is redirected to the dashboard.

---

## API Endpoints

Base URL: `http://127.0.0.1:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/students` | List all students |
| GET | `/api/students/<id>` | Get single student |
| POST | `/api/students` | Add student (JSON body) |
| PUT | `/api/students/<id>` | Update student (JSON body) |
| DELETE | `/api/students/<id>` | Delete student |
| GET | `/api/users` | List all users |

### POST / PUT JSON body example:
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "course": "Python Full Stack"
}
```

### Testing with curl:
```bash
# Get all students
curl http://127.0.0.1:5000/api/students

# Add student
curl -X POST http://127.0.0.1:5000/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@test.com","course":"Flask"}'

# Update student (id=1)
curl -X PUT http://127.0.0.1:5000/api/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob Updated","email":"bob@test.com","course":"Django"}'

# Delete student (id=1)
curl -X DELETE http://127.0.0.1:5000/api/students/1
```

---

## Security Flow

1. **Passwords** are hashed via `werkzeug.security.generate_password_hash` — never stored in plain text.
2. **Session** stores username, role, and user_id on successful login.
3. `@login_required` decorator redirects unauthenticated users to `/login`.
4. `@admin_required` decorator redirects non-admin users to `/dashboard`.
5. **API input validation** — returns 400 if required fields are missing.
6. **Parameterised SQL queries** — prevents SQL injection.

---

## Project Structure

```
flask_task4/
├── app.py               # Main Flask app (routes, decorators, API)
├── requirements.txt
├── database.db          # Auto-created on first run
├── README.md
└── templates/
    ├── base.html        # Shared layout + navigation
    ├── login.html
    ├── register.html
    ├── dashboard.html   # User view (read-only)
    ├── admin.html       # Admin panel (full CRUD + user list)
    ├── add_student.html
    └── edit_student.html
```
# python-task-4
