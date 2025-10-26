from flask import Blueprint, render_template, session, redirect, request, flash, jsonify
from config import get_db_connection
import secrets
from datetime import datetime

hod_bp = Blueprint('hod', __name__, url_prefix='/hod')

def get_department_patterns(department):
    """Generate multiple patterns to match department variations"""
    patterns = [department]
    base_name = department.split('(')[0].strip()
    patterns.append(base_name)
    
    if '&' in base_name:
        patterns.append(base_name.replace('&', 'and'))
    if 'and' in base_name:
        patterns.append(base_name.replace('and', '&'))
    
    if 'computer science' in base_name.lower():
        patterns.append('Computer Science')
        patterns.append('CSE')
    if 'artificial intelligence' in base_name.lower():
        patterns.append('Artificial Intelligence') 
        patterns.append('AI')
    if 'data science' in base_name.lower():
        patterns.append('Data Science')
        patterns.append('DS')
    
    return list(set(patterns))

def generate_faculty_id(name, department):
    """Generate unique faculty ID"""
    dept_code = ''.join([word[0].upper() for word in department.split()[:2]])
    name_initials = ''.join([word[0].upper() for word in name.split()[:2]])
    timestamp = datetime.now().strftime('%m%d')
    random_num = secrets.randbelow(100)
    return f"F{dept_code}{name_initials}{timestamp}{random_num:02d}"

# Dashboard Route
@hod_bp.route('/dashboard')
def dashboard():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    department = session.get('user_department', '')
    patterns = get_department_patterns(department)
    
    placeholders = ','.join(['%s'] * len(patterns))
    
    # Count faculty
    cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE department IN ({placeholders}) AND role = 'faculty' AND status = 'active'", patterns)
    faculty_count = cursor.fetchone()['count']
    
    # Count students
    cursor.execute(f"SELECT COUNT(*) as count FROM students WHERE department IN ({placeholders}) AND status = 'active'", patterns)
    student_count = cursor.fetchone()['count']
    
    # Recent faculty
    cursor.execute(f"SELECT username, name, designation, email, phone FROM users WHERE department IN ({placeholders}) AND role = 'faculty' AND status = 'active' ORDER BY created_at DESC LIMIT 5", patterns)
    recent_faculty = cursor.fetchall()
    
    # Recent students
    cursor.execute(f"SELECT student_id, name, email, phone, admission_date FROM students WHERE department IN ({placeholders}) AND status = 'active' ORDER BY created_at DESC LIMIT 5", patterns)
    recent_students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/dashboard.html',
                         faculty_count=faculty_count,
                         student_count=student_count,
                         recent_faculty=recent_faculty,
                         recent_students=recent_students,
                         department=department)

# Students Management Route
@hod_bp.route('/students')
def students_management():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    department = session.get('user_department', '')
    patterns = get_department_patterns(department)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    placeholders = ','.join(['%s'] * len(patterns))
    cursor.execute(f"SELECT * FROM students WHERE department IN ({placeholders}) ORDER BY created_at DESC", patterns)
    students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/students.html', students=students, department=department)

# Update Student Status Route
@hod_bp.route('/update-student-status', methods=['POST'])
def update_student_status():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    student_id = data.get('student_id')
    new_status = data.get('status')
    hod_department = session.get('user_department', '')
    patterns = get_department_patterns(hod_department)
    
    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ','.join(['%s'] * len(patterns))
        cursor.execute(f"UPDATE students SET status = %s WHERE student_id = %s AND department IN ({placeholders})", 
                      [new_status, student_id] + patterns)
        
        if cursor.rowcount == 0:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Student not found in your department'})
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': f'Student status updated to {new_status}'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# Faculty Management Route
@hod_bp.route('/faculty')
def faculty_management():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    department = session.get('user_department', '')
    patterns = get_department_patterns(department)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    placeholders = ','.join(['%s'] * len(patterns))
    cursor.execute(f"SELECT username, name, email, phone, designation, department, status, date_of_joining, salary, location, aadhar_number, graduation_domain, created_at FROM users WHERE department IN ({placeholders}) AND role = 'faculty' ORDER BY created_at DESC", patterns)
    faculty = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/faculty.html', faculty=faculty, department=department)

# Add Faculty Route
@hod_bp.route('/add-faculty', methods=['POST'])
def add_faculty():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    hod_department = session.get('user_department', '')
    faculty_id = generate_faculty_id(data['name'], hod_department)
    default_password = "faculty123"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (username, password, role, name, email, phone, designation, department, location, salary, date_of_joining, aadhar_number, graduation_domain, password_changed, status, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                      (faculty_id, default_password, 'faculty', data['name'], data['email'], data['phone'], data['designation'], hod_department, data.get('location', ''), data['salary'], data['date_of_joining'], data['aadhar_number'], data['graduation_domain'], False, 'active', session['user_id']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Faculty created successfully', 'faculty_id': faculty_id, 'password': default_password})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

# Get Faculty Details Route
@hod_bp.route('/faculty-details/<username>')
def faculty_details(username):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s AND department = %s AND role = 'faculty'", (username, hod_department))
        faculty = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if faculty:
            return jsonify({'success': True, 'faculty': faculty})
        else:
            return jsonify({'success': False, 'message': 'Faculty not found in your department'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

# Update Faculty Details Route
@hod_bp.route('/update-faculty/<username>', methods=['POST'])
def update_faculty(username):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify faculty belongs to HOD's department before updating
        cursor.execute("SELECT username FROM users WHERE username = %s AND department = %s AND role = 'faculty'", (username, hod_department))
        faculty = cursor.fetchone()
        
        if not faculty:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Faculty not found in your department'})
        
        # Update faculty details
        cursor.execute("""
            UPDATE users 
            SET name = %s, email = %s, phone = %s, designation = %s,
                location = %s, salary = %s, date_of_joining = %s,
                aadhar_number = %s, graduation_domain = %s
            WHERE username = %s AND department = %s AND role = 'faculty'
        """, (
            data['name'], data['email'], data['phone'], data['designation'],
            data.get('location', ''), data['salary'], data['date_of_joining'],
            data['aadhar_number'], data['graduation_domain'],
            username, hod_department
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Faculty details updated successfully!'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# Get Student Details Route
@hod_bp.route('/student-details/<student_id>')
def student_details(student_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    patterns = get_department_patterns(hod_department)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        placeholders = ','.join(['%s'] * len(patterns))
        cursor.execute(f"SELECT * FROM students WHERE student_id = %s AND department IN ({placeholders})", [student_id] + patterns)
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if student:
            return jsonify({'success': True, 'student': student})
        else:
            return jsonify({'success': False, 'message': 'Student not found in your department'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

# Logout Route
@hod_bp.route('/logout')
def hod_logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/login')