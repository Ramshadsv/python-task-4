from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret-key-2025")

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# ─────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    NOT NULL DEFAULT 'user'
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name   TEXT NOT NULL,
            email  TEXT NOT NULL,
            course TEXT NOT NULL
        )
    ''')
    db.commit()

    # Seed admin if not present
    existing = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        db.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', generate_password_hash('admin123'), 'admin')
        )
        db.commit()
    db.close()

# Initialize database when app starts (needed for PythonAnywhere)
init_db()

# ─────────────────────────────────────────
# Decorators
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapper

# ─────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')
        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if existing:
            flash('Username already taken.', 'error')
            db.close()
            return render_template('register.html')
        db.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, 'user')",
            (username, generate_password_hash(password))
        )
        db.commit()
        db.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        db.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['role'] = user['role']
            session['user_id'] = user['id']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
# User dashboard
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    students = db.execute("SELECT * FROM students").fetchall()
    db.close()
    return render_template('dashboard.html', students=students)

# ─────────────────────────────────────────
# Admin panel
# ─────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    users    = db.execute("SELECT id, username, role FROM users").fetchall()
    students = db.execute("SELECT * FROM students").fetchall()
    db.close()
    return render_template('admin.html', users=users, students=students)

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    if request.method == 'POST':
        name   = request.form.get('name', '').strip()
        email  = request.form.get('email', '').strip()
        course = request.form.get('course', '').strip()
        if not name or not email or not course:
            flash('All fields are required.', 'error')
            return render_template('add_student.html')
        db = get_db()
        db.execute("INSERT INTO students (name, email, course) VALUES (?, ?, ?)", (name, email, course))
        db.commit()
        db.close()
        flash('Student added successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_student.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    if not student:
        db.close()
        flash('Student not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        name   = request.form.get('name', '').strip()
        email  = request.form.get('email', '').strip()
        course = request.form.get('course', '').strip()
        db.execute("UPDATE students SET name=?, email=?, course=? WHERE id=?", (name, email, course, id))
        db.commit()
        db.close()
        flash('Student updated.', 'success')
        return redirect(url_for('admin_dashboard'))
    db.close()
    return render_template('edit_student.html', student=student)

@app.route('/admin/delete/<int:id>')
@admin_required
def admin_delete_student(id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (id,))
    db.commit()
    db.close()
    flash('Student deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<int:id>')
@admin_required
def admin_delete_user(id):
    if id == session.get('user_id'):
        flash("You can't delete yourself.", 'error')
        return redirect(url_for('admin_dashboard'))
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (id,))
    db.commit()
    db.close()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

# ─────────────────────────────────────────
# REST API endpoints
# ─────────────────────────────────────────

@app.route('/api/students', methods=['GET'])
def api_get_students():
    db = get_db()
    students = db.execute("SELECT * FROM students").fetchall()
    db.close()
    return jsonify([dict(row) for row in students])

@app.route('/api/students/<int:id>', methods=['GET'])
def api_get_student(id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()
    db.close()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify(dict(student))

@app.route('/api/students', methods=['POST'])
def api_add_student():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    name   = data.get('name', '').strip()
    email  = data.get('email', '').strip()
    course = data.get('course', '').strip()
    if not name or not email or not course:
        return jsonify({'error': 'name, email and course are required'}), 400
    db = get_db()
    cur = db.execute("INSERT INTO students (name, email, course) VALUES (?, ?, ?)", (name, email, course))
    db.commit()
    new_id = cur.lastrowid
    db.close()
    return jsonify({'message': 'Student added successfully', 'id': new_id}), 201

@app.route('/api/students/<int:id>', methods=['PUT'])
def api_update_student(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    name   = data.get('name', '').strip()
    email  = data.get('email', '').strip()
    course = data.get('course', '').strip()
    if not name or not email or not course:
        return jsonify({'error': 'name, email and course are required'}), 400
    db = get_db()
    result = db.execute("SELECT id FROM students WHERE id=?", (id,)).fetchone()
    if not result:
        db.close()
        return jsonify({'error': 'Student not found'}), 404
    db.execute("UPDATE students SET name=?, email=?, course=? WHERE id=?", (name, email, course, id))
    db.commit()
    db.close()
    return jsonify({'message': 'Student updated successfully'})

@app.route('/api/students/<int:id>', methods=['DELETE'])
def api_delete_student(id):
    db = get_db()
    result = db.execute("SELECT id FROM students WHERE id=?", (id,)).fetchone()
    if not result:
        db.close()
        return jsonify({'error': 'Student not found'}), 404
    db.execute("DELETE FROM students WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({'message': 'Student deleted successfully'})

@app.route('/api/users', methods=['GET'])
def api_get_users():
    db = get_db()
    users = db.execute("SELECT id, username, role FROM users").fetchall()
    db.close()
    return jsonify([dict(row) for row in users])

# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=False)