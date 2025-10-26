from flask import Blueprint, render_template, session, redirect, request, jsonify, flash
from config import get_db_connection
from principal.user_management import create_user, get_users

principal_bp = Blueprint('principal', __name__, url_prefix='/principal')

@principal_bp.route('/dashboard')
def dashboard():
    if session.get('user_role') != 'principal':
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM blocks")
    blocks = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM departments")
    departments = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return render_template('principal/dashboard.html', 
                         users=users,
                         blocks=blocks,
                         departments=departments)

@principal_bp.route('/manage-blocks')
def manage_blocks():
    if session.get('user_role') != 'principal':
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM blocks ORDER BY block_code")
    blocks = cursor.fetchall()
    
    cursor.execute("SELECT * FROM rooms ORDER BY block_code, floor, room_number")
    rooms = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('principal/manage_blocks.html', blocks=blocks, rooms=rooms)

@principal_bp.route('/create-block', methods=['POST'])
def create_block():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    block_code = data['block_code'].upper().strip()
    block_name = data['block_name'].strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO blocks (block_code, block_name, created_by) VALUES (%s, %s, %s)",
            (block_code, block_name, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': f'Block {block_code} created successfully'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@principal_bp.route('/create-room', methods=['POST'])
def create_room():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO rooms (block_code, floor, room_number, room_type, created_by) VALUES (%s, %s, %s, %s, %s)",
            (data['block_code'], data['floor'], data['room_number'], data['room_type'], session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Room added successfully'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@principal_bp.route('/user-management')
def user_management():
    if session.get('user_role') != 'principal':
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get blocks and available rooms for work location
    cursor.execute("SELECT * FROM blocks ORDER BY block_code")
    blocks = cursor.fetchall()
    
    cursor.execute("""
        SELECT r.*, b.block_name 
        FROM rooms r 
        JOIN blocks b ON r.block_code = b.block_code 
        WHERE r.status = 'available' 
        ORDER BY r.block_code, r.floor, r.room_number
    """)
    rooms = cursor.fetchall()
    
    # Get existing users (all except principal) - FIXED: use created_at instead of created_date
    cursor.execute("SELECT * FROM users WHERE role != 'principal' ORDER BY created_at DESC")
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('principal/user_management.html', 
                         users=users, 
                         blocks=blocks,
                         rooms=rooms)

@principal_bp.route('/create-user', methods=['POST'])
def create_user_route():
    return create_user()

@principal_bp.route('/get-users', methods=['GET'])
def get_users_route():
    return get_users()

@principal_bp.route('/get-admin-details/<username>')
def get_admin_details(username):
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        admin = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if admin:
            return jsonify({'success': True, 'admin': admin})
        else:
            return jsonify({'success': False, 'message': 'Admin not found'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@principal_bp.route('/update-admin/<username>', methods=['POST'])
def update_admin(username):
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    admin_data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users 
            SET name = %s, email = %s, phone = %s, designation = %s, 
                department = %s, location = %s, salary = %s, 
                date_of_joining = %s, graduation_domain = %s
            WHERE username = %s
        """, (
            admin_data['name'], admin_data['email'], admin_data['phone'],
            admin_data['designation'], admin_data['department'], admin_data['location'],
            admin_data['salary'], admin_data['date_of_joining'], admin_data['graduation_domain'],
            username
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Admin updated successfully!'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@principal_bp.route('/update-hod-assignment', methods=['POST'])
def update_hod_assignment():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    department_id = data['department_id']
    hod_id = data['hod_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First, remove current HOD from any department
        cursor.execute("UPDATE departments SET hod_id = NULL WHERE hod_id = %s", (hod_id,))
        
        # Assign HOD to the new department
        cursor.execute("UPDATE departments SET hod_id = %s WHERE id = %s", (hod_id, department_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'HOD assignment updated successfully!'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@principal_bp.route('/remove-hod/<int:department_id>', methods=['POST'])
def remove_hod(department_id):
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE departments SET hod_id = NULL WHERE id = %s", (department_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'HOD removed successfully!'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)})

@principal_bp.route('/finance-management')
def finance_management():
    if session.get('user_role') != 'principal':
        flash('Access denied', 'error')
        return redirect('/login')
    
    # Add empty finances to avoid template error
    finances = {
        'total_revenue': 0,
        'total_expenses': 0,
        'current_balance': 0
    }
    
    return render_template('principal/finance_management.html', finances=finances)

@principal_bp.route('/department-management')
def department_management():
    if session.get('user_role') != 'principal':
        flash('Access denied', 'error')
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all departments with HOD information
    cursor.execute("""
        SELECT d.*, u.name as hod_name, u.username as hod_username
        FROM departments d 
        LEFT JOIN users u ON d.hod_id = u.id 
        ORDER BY d.name
    """)
    departments = cursor.fetchall()
    
    # Get all HODs for dropdown
    cursor.execute("SELECT id, name, username FROM users WHERE role = 'hod'")
    hods = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('principal/department_management.html', 
                         departments=departments, 
                         hods=hods)

@principal_bp.route('/create-department', methods=['POST'])
def create_department():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    department_name = data['name'].strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Use only the columns that exist in your table
        cursor.execute(
            "INSERT INTO departments (name) VALUES (%s)",
            (department_name,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': f'Department {department_name} created successfully'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@principal_bp.route('/assign-hod', methods=['POST'])
def assign_hod():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    department_id = data['department_id']
    hod_id = data['hod_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE departments SET hod_id = %s WHERE id = %s",
            (hod_id, department_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'HOD assigned successfully'})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@principal_bp.route('/analytics')
def analytics():
    if session.get('user_role') != 'principal':
        flash('Access denied', 'error')
        return redirect('/login')
    return render_template('principal/analytics.html')

@principal_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/login')