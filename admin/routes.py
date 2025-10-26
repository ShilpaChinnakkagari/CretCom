from flask import Blueprint, render_template, session, redirect, request, jsonify, flash
from config import get_db_connection
from datetime import datetime

# BLUEPRINT MUST BE DEFINED FIRST
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# List of allowed admin roles
ALLOWED_ADMIN_ROLES = ['administration_admin', 'college_admin', 'fee_admin', 'placement_admin', 
                       'exam_admin', 'library_admin', 'scholarship_admin', 'events_admin']

# ===== ADMINISTRATION DASHBOARD =====
@admin_bp.route('/dashboard')
def admin_dashboard():
    if session.get('user_role') not in ALLOWED_ADMIN_ROLES:
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Student statistics from students table
    cursor.execute("SELECT COUNT(*) as total_students FROM students WHERE status='active'")
    total_students = cursor.fetchone()['total_students']
    
    cursor.execute("SELECT COUNT(*) as new_today FROM students WHERE DATE(created_at) = CURDATE()")
    new_today = cursor.fetchone()['new_today']
    
    cursor.execute("SELECT COUNT(*) as total_faculty FROM users WHERE role='faculty'")
    total_faculty = cursor.fetchone()['total_faculty']
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_students': total_students,
        'new_today': new_today,
        'total_faculty': total_faculty
    }
    
    return render_template('admin/dashboard.html', stats=stats)

# ===== STUDENT MANAGEMENT =====
@admin_bp.route('/student-management')
def admin_student_management():
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get filter parameters
    department_filter = request.args.get('department', '')
    year_filter = request.args.get('academic_year', '')
    quota_filter = request.args.get('quota', '')
    status_filter = request.args.get('status', 'active')
    
    # Build dynamic query
    query = """
        SELECT student_id, name, email, department, phone, 
               date_of_birth, gender, blood_group, caste,
               father_name, father_phone, mother_name, mother_phone,
               guardian_name, guardian_phone, admission_date, academic_year,
               admission_quota, status, created_at
        FROM students 
        WHERE 1=1
    """
    params = []
    
    if department_filter:
        query += " AND department = %s"
        params.append(department_filter)
    
    if year_filter:
        query += " AND academic_year = %s"
        params.append(year_filter)
    
    if quota_filter:
        query += " AND admission_quota = %s"
        params.append(quota_filter)
    
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    students = cursor.fetchall()
    
    # Get departments for dropdown
    cursor.execute("SELECT name FROM departments")
    departments = cursor.fetchall()
    
    # Get unique academic years for filter
    cursor.execute("SELECT DISTINCT academic_year FROM students ORDER BY academic_year DESC")
    academic_years = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/administration/student_management.html', 
                         students=students, 
                         departments=departments,
                         academic_years=academic_years,
                         current_filters={
                             'department': department_filter,
                             'academic_year': year_filter,
                             'quota': quota_filter,
                             'status': status_filter
                         })

@admin_bp.route('/add-student-record', methods=['POST'])
def admin_add_student_record():
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student_data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Generate student ID: DEPTCODE + YEAR + 3-digit number
        current_year = datetime.now().strftime('%y')
        department_code = student_data['department'][:3].upper()
        
        # Get the next number for this department
        cursor.execute("""
            SELECT COUNT(*) as count FROM students 
            WHERE department=%s AND student_id LIKE %s
        """, (student_data['department'], f'{department_code}{current_year}%'))
        
        count_result = cursor.fetchone()
        next_number = count_result['count'] + 1
        student_id = f"{department_code}{current_year}{str(next_number).zfill(3)}"
        
        # Insert student into students table with all fields
        cursor.execute(
            """INSERT INTO students 
            (student_id, name, email, department, phone, date_of_birth, gender, 
             blood_group, caste, father_name, father_phone, father_occupation,
             mother_name, mother_phone, mother_occupation, guardian_name, 
             guardian_phone, guardian_relation, guardian_address, address,
             city, state, pincode, admission_date, academic_year, admission_quota,
             created_by, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')""",
            (student_id, student_data['name'], student_data['email'], 
             student_data['department'], student_data['phone'], 
             student_data['date_of_birth'], student_data['gender'],
             student_data['blood_group'], student_data['caste'],
             student_data['father_name'], student_data['father_phone'],
             student_data.get('father_occupation', ''),
             student_data['mother_name'], student_data['mother_phone'],
             student_data.get('mother_occupation', ''),
             student_data['guardian_name'], student_data['guardian_phone'],
             student_data['guardian_relation'], student_data['guardian_address'],
             student_data['address'], student_data['city'], student_data['state'],
             student_data['pincode'], student_data['admission_date'],
             student_data['academic_year'], student_data['admission_quota'],
             session['user_id'])
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Student added successfully!',
            'student_id': student_id
        })
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/update-student-record/<student_id>', methods=['POST'])
def admin_update_student_record(student_id):
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    student_data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """UPDATE students 
            SET name=%s, email=%s, department=%s, phone=%s, date_of_birth=%s, 
                gender=%s, blood_group=%s, caste=%s, father_name=%s, father_phone=%s,
                father_occupation=%s, mother_name=%s, mother_phone=%s, mother_occupation=%s,
                guardian_name=%s, guardian_phone=%s, guardian_relation=%s, guardian_address=%s,
                address=%s, city=%s, state=%s, pincode=%s, admission_date=%s, 
                academic_year=%s, admission_quota=%s, updated_at=NOW()
            WHERE student_id=%s""",
            (student_data['name'], student_data['email'], student_data['department'],
             student_data['phone'], student_data['date_of_birth'], student_data['gender'],
             student_data['blood_group'], student_data['caste'], student_data['father_name'],
             student_data['father_phone'], student_data.get('father_occupation', ''),
             student_data['mother_name'], student_data['mother_phone'], student_data.get('mother_occupation', ''),
             student_data['guardian_name'], student_data['guardian_phone'], student_data['guardian_relation'],
             student_data['guardian_address'], student_data['address'], student_data['city'], 
             student_data['state'], student_data['pincode'], student_data['admission_date'],
             student_data['academic_year'], student_data['admission_quota'], student_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Student updated successfully!'})
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/delete-student-record/<student_id>', methods=['POST'])
def admin_delete_student_record(student_id):
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE students SET status='inactive' WHERE student_id=%s",
            (student_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Student deactivated successfully!'})
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/activate-student-record/<student_id>', methods=['POST'])
def admin_activate_student_record(student_id):
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE students SET status='active' WHERE student_id=%s",
            (student_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Student activated successfully!'})
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/get-student-record/<student_id>')
def admin_get_student_record(student_id):
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
        student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if student:
            return jsonify({'success': True, 'student': student})
        else:
            return jsonify({'success': False, 'message': 'Student not found'})
            
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/export-students')
def admin_export_students():
    if session.get('user_role') not in ['administration_admin', 'college_admin']:
        flash('Access denied', 'error')
        return redirect('/login')
    
    # Get filter parameters
    department_filter = request.args.get('department', '')
    year_filter = request.args.get('academic_year', '')
    quota_filter = request.args.get('quota', '')
    status_filter = request.args.get('status', 'active')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Build dynamic query for export
    query = """
        SELECT student_id, name, email, department, phone, date_of_birth, gender,
               blood_group, caste, father_name, father_phone, mother_name, mother_phone,
               guardian_name, guardian_phone, admission_date, academic_year, admission_quota, status
        FROM students 
        WHERE 1=1
    """
    params = []
    
    if department_filter:
        query += " AND department = %s"
        params.append(department_filter)
    
    if year_filter:
        query += " AND academic_year = %s"
        params.append(year_filter)
    
    if quota_filter:
        query += " AND admission_quota = %s"
        params.append(quota_filter)
    
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)
    
    query += " ORDER BY department, academic_year, student_id"
    
    cursor.execute(query, params)
    students = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # For now, return JSON. You can implement CSV/Excel export later
    return jsonify({
        'success': True,
        'students': students,
        'filters': {
            'department': department_filter,
            'academic_year': year_filter,
            'quota': quota_filter,
            'status': status_filter
        }
    })