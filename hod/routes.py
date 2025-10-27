from flask import Blueprint, render_template, session, redirect, request, flash, jsonify, send_file
import os
import secrets
from werkzeug.utils import secure_filename
from datetime import datetime
from config import get_db_connection

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

def generate_ao_id(name, department):
    """Generate unique AO ID"""
    dept_code = ''.join([word[0].upper() for word in department.split()[:2]])
    name_initials = ''.join([word[0].upper() for word in name.split()[:2]])
    timestamp = datetime.now().strftime('%m%d')
    random_num = secrets.randbelow(100)
    return f"AO{dept_code}{name_initials}{timestamp}{random_num:02d}"

# Configure upload folder for task documents
UPLOAD_FOLDER = 'uploads/task_documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ========== DASHBOARD ROUTE ==========
@hod_bp.route('/dashboard')
def hod_dashboard():
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

# ========== STUDENTS MANAGEMENT ROUTES ==========
@hod_bp.route('/students')
def hod_students_management():
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

@hod_bp.route('/update-student-status', methods=['POST'])
def hod_update_student_status():
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

# ========== FACULTY MANAGEMENT ROUTES ==========
@hod_bp.route('/faculty')
def hod_faculty_management():
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

@hod_bp.route('/add-faculty', methods=['POST'])
def hod_add_faculty():
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

@hod_bp.route('/faculty-details/<username>')
def hod_faculty_details(username):
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

@hod_bp.route('/update-faculty/<username>', methods=['POST'])
def hod_update_faculty(username):
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

# ========== STUDENT FILTERING ROUTES ==========
@hod_bp.route('/filter-students')
def hod_filter_students():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter parameters from request
    batch_year = request.args.get('batch_year', '')
    year_of_study = request.args.get('year_of_study', '')
    gender = request.args.get('gender', '')
    section_id = request.args.get('section_id', '')
    management = request.args.get('management', '')
    
    # Build query with filters
    query = """
        SELECT s.*, sec.section_name, u.name as mentor_name 
        FROM students s 
        LEFT JOIN sections sec ON s.section_id = sec.section_id
        LEFT JOIN users u ON s.mentor_id = u.username
        WHERE s.department = %s AND s.status = 'active'
    """
    params = [department]
    
    # Apply filters dynamically
    filters = []
    if batch_year:
        filters.append("s.batch_year = %s")
        params.append(batch_year)
    
    if year_of_study:
        filters.append("s.year_of_study = %s")
        params.append(year_of_study)
    
    if gender:
        filters.append("s.gender = %s")
        params.append(gender)
    
    if section_id:
        filters.append("s.section_id = %s")
        params.append(section_id)
    
    if management:
        filters.append("s.management = %s")
        params.append(management)
    
    # Add filters to query
    if filters:
        query += " AND " + " AND ".join(filters)
    
    query += " ORDER BY s.batch_year DESC, s.name"
    
    cursor.execute(query, params)
    filtered_students = cursor.fetchall()
    
    # Get filter options
    # Get batch years from students - with fallback options
    cursor.execute("SELECT DISTINCT batch_year FROM students WHERE department = %s ORDER BY batch_year DESC", (department,))
    existing_batches = [row['batch_year'] for row in cursor.fetchall()]

    # If no batches exist, provide common academic years as fallback
    if not existing_batches:
        current_year = datetime.now().year
        batch_years = [
            str(current_year - 2),  # 2 years ago
            str(current_year - 1),  # 1 year ago  
            str(current_year),      # Current year
            str(current_year + 1)   # Next year
        ]
    else:
        batch_years = existing_batches
    
    cursor.execute("SELECT DISTINCT year_of_study FROM students WHERE department = %s", (department,))
    year_options = [row['year_of_study'] for row in cursor.fetchall() if row['year_of_study']]
    
    cursor.execute("SELECT DISTINCT gender FROM students WHERE department = %s", (department,))
    genders = [row['gender'] for row in cursor.fetchall() if row['gender']]
    
    cursor.execute("SELECT DISTINCT management FROM students WHERE department = %s", (department,))
    managements = [row['management'] for row in cursor.fetchall() if row['management']]
    
    cursor.execute("SELECT DISTINCT admission_quota FROM students WHERE department = %s", (department,))
    admission_quotas = [row['admission_quota'] for row in cursor.fetchall() if row['admission_quota']]
    
    cursor.execute("SELECT section_id, section_name FROM sections WHERE department = %s", (department,))
    sections = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/filter_students.html',
                         students=filtered_students,
                         batch_years=batch_years,
                         year_options=year_options,
                         genders=genders,
                         managements=managements,
                         admission_quotas=admission_quotas,
                         sections=sections,
                         department=department,
                         current_filters={
                             'batch_year': batch_year,
                             'year_of_study': year_of_study,
                             'gender': gender,
                             'section_id': section_id,
                             'management': management
                         })

@hod_bp.route('/update-student-section', methods=['POST'])
def hod_update_student_section():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    student_id = data.get('student_id')
    section_id = data.get('section_id')
    mentor_id = data.get('mentor_id')
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE students 
            SET section_id = %s, mentor_id = %s 
            WHERE student_id = %s AND department = %s
        """, (section_id, mentor_id, student_id, hod_department))
        
        if cursor.rowcount == 0:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Student not found in your department'})
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Student section and mentor updated successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# ========== SECTIONS MANAGEMENT ROUTES ==========
@hod_bp.route('/sections')
def hod_sections_management():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all sections for the department
    cursor.execute("""
        SELECT s.*, u.name as class_teacher_name 
        FROM sections s 
        LEFT JOIN users u ON s.class_teacher = u.username 
        WHERE s.department = %s 
        ORDER BY s.batch_year DESC, s.section_name
    """, (department,))
    sections = cursor.fetchall()
    
    # Get faculty for class teacher assignment
    cursor.execute("""
        SELECT username, name, designation 
        FROM users 
        WHERE department = %s AND role = 'faculty' AND status = 'active'
        ORDER BY name
    """, (department,))
    faculty = cursor.fetchall()
    
    # Get batch years from students - WITH FALLBACK
    cursor.execute("SELECT DISTINCT batch_year FROM students WHERE department = %s ORDER BY batch_year DESC", (department,))
    existing_batches = [row['batch_year'] for row in cursor.fetchall()]
    
    # If no batches exist, provide common academic years as fallback
    if not existing_batches:
        current_year = datetime.now().year
        batch_years = [
            str(current_year - 2),  # 2 years ago
            str(current_year - 1),  # 1 year ago  
            str(current_year),      # Current year
            str(current_year + 1)   # Next year
        ]
    else:
        batch_years = existing_batches
    
    cursor.close()
    conn.close()
    
    return render_template('hod/sections.html', 
                         sections=sections, 
                         faculty=faculty, 
                         batch_years=batch_years,
                         department=department)

@hod_bp.route('/add-section', methods=['POST'])
def hod_add_section():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    department = session.get('user_department', '')
    
    # Generate section ID
    section_id = f"SECT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO sections 
            (section_id, section_name, department, batch_year, class_teacher, student_range_start, student_range_end, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            section_id,
            data['section_name'],
            department,
            data['batch_year'],
            data.get('class_teacher'),
            data.get('student_range_start'),
            data.get('student_range_end'),
            session['user_id']
        ))
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': 'Section created successfully',
            'section_id': section_id
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/update-section/<section_id>', methods=['POST'])
def hod_update_section(section_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE sections 
            SET section_name = %s, batch_year = %s, class_teacher = %s,
                student_range_start = %s, student_range_end = %s
            WHERE section_id = %s AND department = %s
        """, (
            data['section_name'],
            data['batch_year'],
            data.get('class_teacher'),
            data.get('student_range_start'),
            data.get('student_range_end'),
            section_id, department
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Section updated successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/delete-section/<section_id>', methods=['DELETE'])
def hod_delete_section(section_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First, remove section assignments from students
        cursor.execute("UPDATE students SET section_id = NULL WHERE section_id = %s AND department = %s", 
                      (section_id, department))
        
        # Then delete the section
        cursor.execute("DELETE FROM sections WHERE section_id = %s AND department = %s", 
                      (section_id, department))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Section deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/auto-assign-students', methods=['POST'])
def hod_auto_assign_students():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    data = request.get_json()
    batch_year = data.get('batch_year')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all sections for this batch year
        cursor.execute("""
            SELECT section_id, student_range_start, student_range_end 
            FROM sections 
            WHERE department = %s AND batch_year = %s
        """, (department, batch_year))
        sections = cursor.fetchall()
        
        assigned_count = 0
        
        for section in sections:
            # Assign students based on roll number ranges
            cursor.execute("""
                UPDATE students 
                SET section_id = %s 
                WHERE department = %s AND batch_year = %s 
                AND student_id BETWEEN %s AND %s
            """, (section['section_id'], department, batch_year, 
                  section['student_range_start'], section['student_range_end']))
            
            assigned_count += cursor.rowcount
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': f'Automatically assigned {assigned_count} students to sections'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/assign-mentor', methods=['POST'])
def hod_assign_mentor():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update students with mentor based on roll number range
        cursor.execute("""
            UPDATE students 
            SET mentor_id = %s 
            WHERE department = %s AND batch_year = %s 
            AND student_id BETWEEN %s AND %s
        """, (
            data['mentor_id'],
            department,
            data['batch_year'],
            data['student_range_start'],
            data['student_range_end']
        ))
        
        assigned_count = cursor.rowcount
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Mentor assigned to {assigned_count} students'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/get-mentor-assignments')
def hod_get_mentor_assignments():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    batch_year = request.args.get('batch_year', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get mentor assignments summary
    query = """
        SELECT mentor_id, u.name as mentor_name, 
               MIN(student_id) as range_start, MAX(student_id) as range_end,
               COUNT(*) as student_count
        FROM students s
        LEFT JOIN users u ON s.mentor_id = u.username
        WHERE s.department = %s AND s.mentor_id IS NOT NULL
    """
    params = [department]
    
    if batch_year:
        query += " AND s.batch_year = %s"
        params.append(batch_year)
    
    query += " GROUP BY mentor_id, u.name ORDER BY range_start"
    
    cursor.execute(query, params)
    assignments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'assignments': assignments})

@hod_bp.route('/get-section-students/<section_id>')
def hod_get_section_students(section_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get section name
        cursor.execute("SELECT section_name FROM sections WHERE section_id = %s AND department = %s", 
                      (section_id, department))
        section = cursor.fetchone()
        
        if not section:
            return jsonify({'success': False, 'message': 'Section not found'})
        
        # Get students in this section
        cursor.execute("""
            SELECT s.student_id, s.name, u.name as mentor_name
            FROM students s
            LEFT JOIN users u ON s.mentor_id = u.username
            WHERE s.section_id = %s AND s.department = %s
            ORDER BY s.student_id
        """, (section_id, department))
        students = cursor.fetchall()
        
        return jsonify({
            'success': True, 
            'students': students,
            'section_name': section['section_name']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

# ========== AO MANAGEMENT ROUTES ==========
@hod_bp.route('/ao-management')
def hod_ao_management():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all AO staff from HOD's department
    cursor.execute("SELECT * FROM ao_staff WHERE department = %s ORDER BY created_at DESC", (department,))
    ao_staff = cursor.fetchall()
    
    # Get assigned tasks for the department
    cursor.execute("""
        SELECT t.*, ao.name as ao_name, ao.ao_id,
               CASE 
                   WHEN t.status = 'pending' THEN '🔴 Pending'
                   WHEN t.status = 'in_progress' THEN '🟡 In Progress' 
                   WHEN t.status = 'completed' THEN '🟢 Completed'
                   WHEN t.status = 'cancelled' THEN '⚫ Cancelled'
               END as status_display,
               CASE
                   WHEN t.priority = 'low' THEN '🟢 Low'
                   WHEN t.priority = 'medium' THEN '🟡 Medium'
                   WHEN t.priority = 'high' THEN '🟠 High'
                   WHEN t.priority = 'urgent' THEN '🔴 Urgent'
               END as priority_display
        FROM ao_tasks t 
        JOIN ao_staff ao ON t.ao_id = ao.ao_id 
        WHERE ao.department = %s 
        ORDER BY t.created_at DESC
    """, (department,))
    assigned_tasks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/ao_management.html', 
                         ao_staff=ao_staff, 
                         assigned_tasks=assigned_tasks,
                         department=department)

@hod_bp.route('/add-ao', methods=['POST'])
def hod_add_ao():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    hod_department = session.get('user_department', '')
    
    # Generate AO ID
    ao_id = generate_ao_id(data['name'], hod_department)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO ao_staff 
            (ao_id, name, email, phone, aadhar_number, address, caste, 
             department, salary, work_location, date_of_joining, 
             graduation_domain, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ao_id, data['name'], data['email'], data['phone'],
            data['aadhar_number'], data.get('address', ''), data.get('caste', ''),
            hod_department, data['salary'],
            data.get('work_location', ''), data['date_of_joining'],
            data['graduation_domain'], 'active', session['user_id']
        ))
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': 'AO Staff created successfully',
            'ao_id': ao_id
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/get-ao-details/<ao_id>')
def hod_get_ao_details(ao_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM ao_staff WHERE ao_id = %s AND department = %s", (ao_id, hod_department))
        ao_staff = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if ao_staff:
            return jsonify({'success': True, 'ao_staff': ao_staff})
        else:
            return jsonify({'success': False, 'message': 'AO Staff not found in your department'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@hod_bp.route('/update-ao/<ao_id>', methods=['POST'])
def hod_update_ao(ao_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verify AO belongs to HOD's department before updating
        cursor.execute("SELECT ao_id FROM ao_staff WHERE ao_id = %s AND department = %s", (ao_id, hod_department))
        ao_staff = cursor.fetchone()
        
        if not ao_staff:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'AO Staff not found in your department'})
        
        # Update AO details
        cursor.execute("""
            UPDATE ao_staff 
            SET name = %s, email = %s, phone = %s,
                work_location = %s, salary = %s, date_of_joining = %s,
                aadhar_number = %s, graduation_domain = %s, address = %s,
                caste = %s
            WHERE ao_id = %s AND department = %s
        """, (
            data['name'], data['email'], data['phone'],
            data.get('work_location', ''), data['salary'], data['date_of_joining'],
            data['aadhar_number'], data['graduation_domain'], data.get('address', ''),
            data.get('caste', ''), ao_id, hod_department
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'AO Staff details updated successfully!'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@hod_bp.route('/update-ao-status', methods=['POST'])
def hod_update_ao_status():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    ao_id = data.get('ao_id')
    new_status = data.get('status')
    hod_department = session.get('user_department', '')
    
    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE ao_staff SET status = %s WHERE ao_id = %s AND department = %s", 
                      (new_status, ao_id, hod_department))
        
        if cursor.rowcount == 0:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'AO Staff not found in your department'})
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': f'AO Staff status updated to {new_status}'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# ========== TASK MANAGEMENT ROUTES ==========
@hod_bp.route('/assign-task-to-ao', methods=['POST'])
def hod_assign_task_to_ao():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    
    # Generate task ID
    task_id = f"TASK{datetime.now().strftime('%Y%m%d%H%M%S')}"
    document_path = None
    
    # Handle file upload if provided
    if 'document' in request.files:
        file = request.files['document']
        if file and file.filename != '':
            # Create upload directory if not exists
            upload_folder = 'uploads/task_documents'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{task_id}_{filename}"
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            document_path = file_path
    
    # Get form data
    ao_id = request.form.get('ao_id')
    subject = request.form.get('subject')
    task_description = request.form.get('task_description')
    priority = request.form.get('priority', 'medium')
    deadline = request.form.get('deadline')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO ao_tasks 
            (task_id, ao_id, subject, task_description, priority, assigned_by, deadline, document_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            task_id, 
            ao_id,
            subject,
            task_description,
            priority,
            session['user_id'],
            deadline if deadline else None,
            document_path
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task assigned successfully', 'task_id': task_id})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@hod_bp.route('/get-task-details/<task_id>')
def hod_get_task_details(task_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT t.*, ao.name as ao_name, ao.ao_id,
               CASE 
                   WHEN t.status = 'pending' THEN '🔴 Pending'
                   WHEN t.status = 'in_progress' THEN '🟡 In Progress' 
                   WHEN t.status = 'completed' THEN '🟢 Completed'
                   WHEN t.status = 'cancelled' THEN '⚫ Cancelled'
               END as status_display,
               CASE
                   WHEN t.priority = 'low' THEN '🟢 Low'
                   WHEN t.priority = 'medium' THEN '🟡 Medium'
                   WHEN t.priority = 'high' THEN '🟠 High'
                   WHEN t.priority = 'urgent' THEN '🔴 Urgent'
               END as priority_display
        FROM ao_tasks t 
        JOIN ao_staff ao ON t.ao_id = ao.ao_id 
        WHERE t.task_id = %s AND ao.department = %s
    """, (task_id, hod_department))
    
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if task:
        return jsonify({'success': True, 'task': task})
    else:
        return jsonify({'success': False, 'message': 'Task not found'})

@hod_bp.route('/delete-task/<task_id>', methods=['DELETE'])
def hod_delete_task(task_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE t FROM ao_tasks t 
            JOIN ao_staff ao ON t.ao_id = ao.ao_id 
            WHERE t.task_id = %s AND ao.department = %s
        """, (task_id, hod_department))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@hod_bp.route('/get-ao-list')
def hod_get_ao_list():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT ao_id, name FROM ao_staff WHERE department = %s AND status = 'active' ORDER BY name", (hod_department,))
    ao_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'ao_list': ao_list})

@hod_bp.route('/student-details/<student_id>')
def hod_student_details(student_id):
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

# ========== LOGOUT ROUTE ==========
@hod_bp.route('/logout')
def hod_logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/login')