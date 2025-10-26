from flask import request, jsonify, session
from config import get_db_connection
import secrets
from datetime import datetime

def generate_user_id(role, name):
    prefix = {
        'fee_admin': 'FA', 'placement_admin': 'PA', 'exam_admin': 'EA',
        'library_admin': 'LA', 'club_admin': 'CA', 'grievance_admin': 'GA',
        'research_admin': 'RA', 'events_admin': 'EVA', 'scholarship_admin': 'SA',
        'international_admin': 'IA', 'welfare_admin': 'WA'
    }.get(role, 'AD')
    
    name_initials = ''.join([word[0].upper() for word in name.split()[:2]])
    timestamp = datetime.now().strftime('%m%d')
    random_num = secrets.randbelow(100)
    
    return f"{prefix}{name_initials}{timestamp}{random_num:02d}"

def create_user():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    
    # Generate user ID and default password
    user_id = generate_user_id(data['role'], data['name'])
    default_password = "admin123"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO users 
            (username, password, role, name, email, phone, designation, 
             department, location, salary, date_of_joining, aadhar_number, 
             graduation_domain, password_changed, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, default_password, data['role'], data['name'], 
            data['email'], data['phone'], data['designation'],
            data['department'], data['location'], data['salary'],
            data['date_of_joining'], data['aadhar_number'],
            data['graduation_domain'], False, 'active', session['user_id']
        ))
        
        conn.commit()
        return jsonify({
            'success': True, 
            'message': 'Admin created successfully',
            'user_id': user_id,
            'password': default_password
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    finally:
        cursor.close()
        conn.close()

def get_users():
    if session.get('user_role') != 'principal':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT username, name, role, designation, department, email, 
                   phone, salary, status, password_changed, location,
                   date_of_joining
            FROM users 
            WHERE role != 'principal'
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        return jsonify({'success': True, 'users': users})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()