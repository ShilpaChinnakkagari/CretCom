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

# AO Management Routes
@hod_bp.route('/ao-management')
def ao_management():
    if session.get('user_role') != 'hod':
        flash('Access denied', 'error')
        return redirect('/login')
    
    department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all AO staff from HOD's department
    cursor.execute("SELECT * FROM ao_staff WHERE department = %s ORDER BY created_at DESC", (department,))
    ao_staff = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/ao_management.html', ao_staff=ao_staff, department=department)

# HOD Task Management Routes
@hod_bp.route('/assign-task', methods=['POST'])
def assign_task():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    hod_department = session.get('user_department', '')
    
    # Generate task ID
    task_id = f"TASK{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO ao_tasks 
            (task_id, ao_id, subject, task_description, priority, assigned_by, deadline)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            task_id, data['ao_id'], data['subject'], data['task_description'],
            data.get('priority', 'medium'), session['user_id'], data.get('deadline')
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

@hod_bp.route('/get-ao-list')
def get_ao_list():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT ao_id, name, email FROM ao_staff WHERE department = %s AND status = 'active'", (hod_department,))
    ao_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'ao_list': ao_list})

@hod_bp.route('/hod-tasks')
def hod_tasks():
    if session.get('user_role') != 'hod':
        return redirect('/login')
    
    hod_department = session.get('user_department', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT t.*, ao.name as ao_name 
        FROM ao_tasks t 
        JOIN ao_staff ao ON t.ao_id = ao.ao_id 
        WHERE ao.department = %s 
        ORDER BY t.created_at DESC
    """, (hod_department,))
    tasks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/tasks.html', tasks=tasks)

# HOD Document Upload Route
@hod_bp.route('/upload-document', methods=['POST'])
def upload_document():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    if 'document' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        # Create uploads directory if not exists
        upload_dir = 'uploads/ao_documents'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        document_id = f"DOC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ao_id = request.form.get('ao_id', None)
        department = session.get('user_department')
        description = request.form.get('description', '')
        
        cursor.execute("""
            INSERT INTO ao_documents 
            (document_id, ao_id, department, filename, original_filename, file_path, 
             file_type, file_size, description, uploaded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            document_id, ao_id, department, unique_filename, filename, file_path,
            file.content_type, os.path.getsize(file_path), description, session['user_id']
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Document uploaded successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid file type'})

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update the add_ao function to include username and password
@hod_bp.route('/add-ao', methods=['POST'])
def add_ao():
    if session.get('user_role') != 'hod':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    hod_department = session.get('user_department', '')
    
    # Generate AO ID and username
    ao_id = generate_ao_id(data['name'], hod_department)
    username = ao_id.lower()  # Use AO ID as username
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO ao_staff 
            (ao_id, username, name, email, phone, aadhar_number, address, caste, 
             department, salary, work_location, date_of_joining, 
             graduation_domain, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ao_id, username, data['name'], data['email'], data['phone'],
            data['aadhar_number'], data.get('address', ''), data.get('caste', ''),
            hod_department, data['salary'],
            data.get('work_location', ''), data['date_of_joining'],
            data['graduation_domain'], 'active', session['user_id']
        ))
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': 'AO Staff created successfully',
            'ao_id': ao_id,
            'username': username,
            'password': 'ao123456'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

@hod_bp.route('/get-ao-details/<ao_id>')
def get_ao_details(ao_id):
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
def update_ao(ao_id):
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
            SET name = %s, email = %s, phone = %s, designation = %s,
                work_location = %s, salary = %s, date_of_joining = %s,
                aadhar_number = %s, graduation_domain = %s, address = %s,
                caste = %s
            WHERE ao_id = %s AND department = %s
        """, (
            data['name'], data['email'], data['phone'], data['designation'],
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
def update_ao_status():
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

def generate_ao_id(name, department):
    """Generate unique AO ID"""
    dept_code = ''.join([word[0].upper() for word in department.split()[:2]])
    name_initials = ''.join([word[0].upper() for word in name.split()[:2]])
    timestamp = datetime.now().strftime('%m%d')
    random_num = secrets.randbelow(100)
    return f"AO{dept_code}{name_initials}{timestamp}{random_num:02d}"


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