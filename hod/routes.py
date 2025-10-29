from flask import Blueprint, render_template, session, redirect, request, flash, jsonify, send_file
import os
import secrets
from werkzeug.utils import secure_filename
from datetime import datetime
from config import get_db_connection

hod_bp = Blueprint('hod', __name__, url_prefix='/hod')

def get_department_patterns(department):
    """Generate multiple patterns to match department variations"""
    patterns = []
    
    # Always include the exact department name
    patterns.append(department)
    
    # Extract base name by removing text in parentheses
    base_name = department.split('(')[0].strip()
    patterns.append(base_name)
    
    # Remove common suffixes and create variations
    suffixes = ['department', 'dept', 'engineering', 'engg', 'technology', 'tech', 
                'science', 'studies', 'management', 'commerce']
    
    # Create variations without common suffixes
    base_variations = [base_name]
    for suffix in suffixes:
        if base_name.lower().endswith(suffix):
            base_without_suffix = base_name[:-len(suffix)].strip()
            base_variations.append(base_without_suffix)
            break
    
    # Generate all possible combinations
    for base in base_variations:
        patterns.extend([
            base,
            base.upper(),
            base.lower(),
            base.title(),
            base.replace(' ', ''),
            base.replace(' ', '-'),
            base.replace(' & ', ' and '),
            base.replace(' and ', ' & ')
        ])
    
    # Extract abbreviations from parentheses if present
    if '(' in department and ')' in department:
        import re
        abbreviations = re.findall(r'\(([^)]+)\)', department)
        for abbr in abbreviations:
            patterns.extend([
                abbr,
                abbr.upper(),
                abbr.lower()
            ])
    
    # Remove duplicates and empty strings, then return
    return list(set([p for p in patterns if p]))

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
    
    # FIXED QUERY - Specify table names for ambiguous columns
    query = """
        SELECT s.student_id, s.name, s.batch_start_year, s.batch_end_year, s.year_of_study,
               s.gender, s.section_id, s.management, s.admission_quota,
               sec.section_name, u.name as mentor_name
        FROM students s
        LEFT JOIN sections sec ON s.section_id = sec.section_id
        LEFT JOIN users u ON s.mentor_id = u.username
        WHERE s.department = 'Artificial Intelligence' AND s.status = 'active'
        ORDER BY s.batch_start_year DESC, s.student_id
    """
    
    cursor.execute(query)
    students = cursor.fetchall()
    
    # Rest of your code remains the same...
    cursor.execute("SELECT DISTINCT batch_start_year FROM students WHERE department = 'Artificial Intelligence' AND batch_start_year IS NOT NULL ORDER BY batch_start_year DESC")
    batch_start_years = [row['batch_start_year'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT batch_end_year FROM students WHERE department = 'Artificial Intelligence' AND batch_end_year IS NOT NULL ORDER BY batch_end_year DESC")
    batch_end_years = [row['batch_end_year'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT year_of_study FROM students WHERE department = 'Artificial Intelligence' AND year_of_study IS NOT NULL ORDER BY year_of_study")
    year_options = [row['year_of_study'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT gender FROM students WHERE department = 'Artificial Intelligence' AND gender IS NOT NULL")
    genders = [row['gender'] for row in cursor.fetchall()]
    
    cursor.execute("SELECT section_id, section_name FROM sections WHERE department = %s ORDER BY section_name", (department,))
    sections = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Combine batch years for display
    batch_years_data = []
    for start_year in batch_start_years:
        for end_year in batch_end_years:
            if end_year - start_year == 4:  # Typical 4-year program
                batch_years_data.append({'batch_start_year': start_year, 'batch_end_year': end_year})
    
    return render_template('hod/filter_students.html',
                         students=students,
                         batch_years_data=batch_years_data,
                         year_options=year_options,
                         genders=genders,
                         sections=sections,
                         managements=['Regular', 'Management'],
                         admission_quotas=['Management', 'Convenor', 'NRI', 'Other'],
                         current_filters={},
                         department=department)

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
    
    # Get batch years from students using the new batch_start_year and batch_end_year fields
    cursor.execute("""
        SELECT DISTINCT 
            batch_start_year,
            batch_end_year
        FROM students 
        WHERE department = %s AND status = 'active' 
        AND batch_start_year IS NOT NULL AND batch_end_year IS NOT NULL
        ORDER BY batch_start_year DESC
    """, (department,))
    batch_years_data = cursor.fetchall()
    
    # Format batch years for display in sections
    batch_years = []
    for batch in batch_years_data:
        if batch['batch_start_year'] and batch['batch_end_year']:
            batch_years.append(f"{batch['batch_start_year']}-{batch['batch_end_year']}")

    # If no batches exist, provide common academic years as fallback
    if not batch_years:
        current_year = datetime.now().year
        batch_years = [
            f"{current_year}-{current_year+4}",
            f"{current_year-1}-{current_year+3}",
            f"{current_year-2}-{current_year+2}",
            f"{current_year+1}-{current_year+5}"
        ]
    
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
        # 1. Create the section
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
        
        # 2. AUTO-ASSIGN STUDENTS based on range
        if data.get('student_range_start') and data.get('student_range_end'):
            cursor.execute("""
                UPDATE students 
                SET section_id = %s, mentor_id = %s
                WHERE department = %s 
                AND student_id BETWEEN %s AND %s
                AND status = 'active'
            """, (
                section_id,
                data.get('class_teacher'),  # Also assign as mentor
                'Artificial Intelligence',  # Use base department name
                data.get('student_range_start'),
                data.get('student_range_end')
            ))
            assigned_count = cursor.rowcount
        else:
            assigned_count = 0
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': f'Section created successfully! {assigned_count} students assigned.',
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
        # 1. Update section details
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
        
        # 2. RE-ASSIGN STUDENTS based on new range and batch year
        assigned_count = 0
        if data.get('student_range_start') and data.get('student_range_end'):
            # First, remove all students from this section
            cursor.execute("""
                UPDATE students 
                SET section_id = NULL 
                WHERE section_id = %s AND department = %s
            """, (section_id, 'Artificial Intelligence'))
            
            # Then assign students based on NEW range and batch year
            batch_start_year = data['batch_year'].split('-')[0]
            cursor.execute("""
                UPDATE students 
                SET section_id = %s 
                WHERE department = %s 
                AND batch_start_year = %s  # CRITICAL: Match batch year
                AND student_id BETWEEN %s AND %s
                AND status = 'active'
            """, (
                section_id,
                'Artificial Intelligence',
                batch_start_year,  # Only assign students from this batch
                data.get('student_range_start'),
                data.get('student_range_end')
            ))
            assigned_count = cursor.rowcount
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': f'Section updated successfully! {assigned_count} students re-assigned.'
        })
        
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
            # Assign students based on roll number ranges - FIXED: using batch_start_year instead of batch_year
            cursor.execute("""
                UPDATE students 
                SET section_id = %s 
                WHERE department = %s AND batch_start_year = %s 
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
        # Extract batch start year from the selected batch (e.g., "2024-2028" -> 2024)
        selected_batch_start = int(data['batch_year'].split('-')[0])
        
        print(f"DEBUG: Assigning mentor for batch {data['batch_year']} (start year: {selected_batch_start})")
        print(f"DEBUG: Student range: {data['student_range_start']} to {data['student_range_end']}")
        
        # First, count how many students match BOTH range AND batch year
        cursor.execute("""
            SELECT COUNT(*) 
            FROM students 
            WHERE department = %s 
            AND batch_start_year = %s  # MUST match selected batch
            AND student_id BETWEEN %s AND %s
            AND status = 'active'
        """, (
            'Artificial Intelligence',
            selected_batch_start,  # This is CRITICAL
            data['student_range_start'],
            data['student_range_end']
        ))
        student_count = cursor.fetchone()[0]
        
        print(f"DEBUG: Found {student_count} students in batch {selected_batch_start}")
        
        # Update students with mentor - ONLY if they match the batch year
        cursor.execute("""
            UPDATE students 
            SET mentor_id = %s 
            WHERE department = %s 
            AND batch_start_year = %s  # MUST match selected batch
            AND student_id BETWEEN %s AND %s
            AND status = 'active'
        """, (
            data['mentor_id'],
            'Artificial Intelligence',
            selected_batch_start,  # This is CRITICAL
            data['student_range_start'],
            data['student_range_end']
        ))
        
        updated_count = cursor.rowcount
        print(f"DEBUG: Actually updated {updated_count} students")
        
        # Save to mentor_assignments table
        cursor.execute("""
            INSERT INTO mentor_assignments 
            (mentor_id, batch_year, student_range_start, student_range_end, student_count, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['mentor_id'],
            data['batch_year'],
            data['student_range_start'],
            data['student_range_end'],
            student_count,  # Use the count from the SELECT query
            session['user_id']
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Mentor assigned to {student_count} students from batch {data["batch_year"]} successfully!'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"ERROR in assign-mentor: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/assign-class-teacher', methods=['POST'])
def hod_assign_class_teacher():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    section_id = data.get('section_id')
    class_teacher = data.get('class_teacher')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update section with class teacher
        cursor.execute("""
            UPDATE sections 
            SET class_teacher = %s 
            WHERE section_id = %s AND department = %s
        """, (class_teacher, section_id, session.get('user_department')))
        
        # Update all students in this section to have this teacher as mentor
        cursor.execute("""
            UPDATE students 
            SET mentor_id = %s 
            WHERE section_id = %s AND department = %s
        """, (class_teacher, section_id, session.get('user_department')))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Class teacher assigned successfully!'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/get-faculty-for-section')
def hod_get_faculty_for_section():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT username, name 
            FROM users 
            WHERE department = %s AND role = 'faculty' AND status = 'active'
            ORDER BY name
        """, (department,))
        faculty = cursor.fetchall()
        
        return jsonify({'success': True, 'faculty': faculty})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/get-mentor-assignment/<int:assignment_id>')
def hod_get_mentor_assignment(assignment_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM mentor_assignments WHERE id = %s
        """, (assignment_id,))
        
        assignment = cursor.fetchone()
        return jsonify({'success': True, 'assignment': assignment})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()



@hod_bp.route('/get-section-students/<section_id>')
def hod_get_section_students(section_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get section details including batch_year
        cursor.execute("""
            SELECT section_name, class_teacher, student_range_start, student_range_end, batch_year
            FROM sections WHERE section_id = %s AND department = %s
        """, (section_id, department))
        section = cursor.fetchone()
        
        if not section:
            return jsonify({'success': False, 'message': 'Section not found'})
        
        # Extract batch start year from section's batch_year
        section_batch_start = int(section['batch_year'].split('-')[0]) if section['batch_year'] else None
        
        # Get students that are ACTUALLY ASSIGNED to this section
        query = """
            SELECT s.student_id, s.name, s.batch_start_year, s.batch_end_year,
                   s.section_id, u.name as mentor_name
            FROM students s
            LEFT JOIN users u ON s.mentor_id = u.username
            WHERE s.section_id = %s  # Only students assigned to this section
            AND s.status = 'active'
            ORDER BY s.student_id
        """
        
        cursor.execute(query, (section_id,))
        students = cursor.fetchall()
        
        return jsonify({
            'success': True, 
            'students': students,
            'section_name': section['section_name'],
            'class_teacher': section['class_teacher'] or 'Not Assigned',
            'range_info': f"{section['student_range_start']} - {section['student_range_end']} (Batch: {section['batch_year']})"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/get-mentor-students/<mentor_id>')
def hod_get_mentor_students(mentor_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get mentor name
        cursor.execute("SELECT name FROM users WHERE username = %s", (mentor_id,))
        mentor = cursor.fetchone()
        
        # Get students assigned to this mentor - show ALL regardless of batch
        cursor.execute("""
            SELECT s.student_id, s.name, s.batch_start_year, s.batch_end_year,
                   sec.section_name
            FROM students s
            LEFT JOIN sections sec ON s.section_id = sec.section_id
            WHERE s.mentor_id = %s AND s.department = %s AND s.status = 'active'
            ORDER BY s.batch_start_year, s.student_id
        """, (mentor_id, 'Artificial Intelligence'))
        students = cursor.fetchall()
        
        return jsonify({
            'success': True, 
            'students': students,
            'mentor_name': mentor['name'] if mentor else 'Unknown Mentor'
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

@hod_bp.route('/get-all-mentor-assignments')
def hod_get_all_mentor_assignments():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all mentor assignments from the mentor_assignments table
        cursor.execute("""
            SELECT ma.id, ma.mentor_id, u.name as mentor_name, ma.batch_year,
                   ma.student_range_start, ma.student_range_end, ma.student_count,
                   ma.created_at
            FROM mentor_assignments ma
            JOIN users u ON ma.mentor_id = u.username
            WHERE u.department = %s
            ORDER BY ma.created_at DESC
        """, (department,))
        
        assignments = cursor.fetchall()
        return jsonify({'success': True, 'assignments': assignments})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

        
@hod_bp.route('/update-mentor-assignment/<int:assignment_id>', methods=['POST'])
def hod_update_mentor_assignment(assignment_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update mentor assignment
        cursor.execute("""
            UPDATE mentor_assignments 
            SET mentor_id = %s, batch_year = %s,
                student_range_start = %s, student_range_end = %s
            WHERE id = %s
        """, (
            data['mentor_id'],
            data['batch_year'],
            data['student_range_start'],
            data['student_range_end'],
            assignment_id
        ))
        
        # Update students with new mentor
        batch_start_year = data['batch_year'].split('-')[0]
        cursor.execute("""
            UPDATE students 
            SET mentor_id = %s 
            WHERE department = %s 
            AND batch_start_year = %s
            AND student_id BETWEEN %s AND %s
            AND status = 'active'
        """, (
            data['mentor_id'],
            'Artificial Intelligence',
            batch_start_year,
            data['student_range_start'],
            data['student_range_end']
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Mentor assignment updated successfully!'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/delete-mentor-assignment/<int:assignment_id>', methods=['DELETE'])
def hod_delete_mentor_assignment(assignment_id):
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get assignment details before deleting
        cursor.execute("""
            SELECT mentor_id, batch_year, student_range_start, student_range_end 
            FROM mentor_assignments WHERE id = %s
        """, (assignment_id,))
        assignment = cursor.fetchone()
        
        if assignment:
            # Remove mentor from students
            batch_start_year = assignment[1].split('-')[0]
            cursor.execute("""
                UPDATE students 
                SET mentor_id = NULL 
                WHERE department = %s 
                AND batch_start_year = %s
                AND student_id BETWEEN %s AND %s
                AND mentor_id = %s
            """, (
                'Artificial Intelligence',
                batch_start_year,
                assignment[2],  # student_range_start
                assignment[3],  # student_range_end  
                assignment[0]   # mentor_id
            ))
        
        # Delete the assignment
        cursor.execute("DELETE FROM mentor_assignments WHERE id = %s", (assignment_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Mentor assignment deleted successfully!'})
        
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