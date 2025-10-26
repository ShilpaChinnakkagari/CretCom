from flask import Blueprint, render_template, session, redirect, request, flash, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from config import get_db_connection

# Create blueprint with URL prefix /hod/ao
ao_bp = Blueprint('ao', __name__, url_prefix='/hod/ao')

# AO Login Route
@ao_bp.route('/login', methods=['GET', 'POST'])
def ao_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM ao_staff WHERE username = %s AND password = %s AND status = 'active'", (username, password))
        ao_user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if ao_user:
            session['user_id'] = ao_user['ao_id']
            session['username'] = ao_user['username']
            session['user_role'] = 'ao'
            session['user_name'] = ao_user['name']
            session['user_department'] = ao_user['department']
            
            # Redirect to password change if first login
            if not ao_user.get('password_changed'):
                return redirect('/hod/ao/change-password')
            
            return redirect('/hod/ao/tasks')  # Redirect directly to tasks
        else:
            flash('Invalid credentials or account inactive', 'error')
    
    return render_template('hod/ao/login.html')

# AO Change Password Route
@ao_bp.route('/change-password', methods=['GET', 'POST'])
def ao_change_password():
    if session.get('user_role') != 'ao':
        return redirect('/hod/ao/login')
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect('/hod/ao/change-password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify current password
        cursor.execute("SELECT * FROM ao_staff WHERE ao_id = %s AND password = %s", (session['user_id'], current_password))
        ao_user = cursor.fetchone()
        
        if not ao_user:
            flash('Current password is incorrect', 'error')
            cursor.close()
            conn.close()
            return redirect('/hod/ao/change-password')
        
        # Update password
        cursor.execute("UPDATE ao_staff SET password = %s, password_changed = TRUE WHERE ao_id = %s", (new_password, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Password changed successfully!', 'success')
        return redirect('/hod/ao/tasks')
    
    return render_template('hod/ao/change_password.html')

# AO Tasks Management Route
@ao_bp.route('/tasks')
def ao_tasks():
    if session.get('user_role') != 'ao':
        return redirect('/hod/ao/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get AO details
    cursor.execute("SELECT * FROM ao_staff WHERE ao_id = %s", (session['user_id'],))
    ao_details = cursor.fetchone()
    
    # Get tasks
    cursor.execute("""
        SELECT t.*, h.name as assigned_by 
        FROM ao_tasks t 
        LEFT JOIN users h ON t.assigned_by = h.username 
        WHERE t.ao_id = %s 
        ORDER BY t.created_at DESC
    """, (session['user_id'],))
    tasks = cursor.fetchall()
    
    # Task counts for stats
    cursor.execute("SELECT COUNT(*) as total_tasks FROM ao_tasks WHERE ao_id = %s", (session['user_id'],))
    total_tasks = cursor.fetchone()['total_tasks']
    
    cursor.execute("SELECT COUNT(*) as pending_tasks FROM ao_tasks WHERE ao_id = %s AND status = 'pending'", (session['user_id'],))
    pending_tasks = cursor.fetchone()['pending_tasks']
    
    cursor.execute("SELECT COUNT(*) as completed_tasks FROM ao_tasks WHERE ao_id = %s AND status = 'completed'", (session['user_id'],))
    completed_tasks = cursor.fetchone()['completed_tasks']
    
    cursor.close()
    conn.close()
    
    return render_template('hod/ao/tasks.html', 
                         tasks=tasks, 
                         ao_details=ao_details,
                         total_tasks=total_tasks,
                         pending_tasks=pending_tasks,
                         completed_tasks=completed_tasks)

# Update Task Status Route
@ao_bp.route('/update-task-status', methods=['POST'])
def update_task_status():
    if session.get('user_role') != 'ao':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    task_id = data.get('task_id')
    status = data.get('status')
    remarks = data.get('remarks', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE ao_tasks 
            SET status = %s, remarks = %s, updated_at = %s 
            WHERE id = %s AND ao_id = %s
        """, (status, remarks, datetime.now(), task_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Task status updated successfully'})
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# AO Documents Route
@ao_bp.route('/documents')
def ao_documents():
    if session.get('user_role') != 'ao':
        return redirect('/hod/ao/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT d.*, h.name as uploaded_by 
        FROM ao_documents d 
        LEFT JOIN users h ON d.uploaded_by = h.username 
        WHERE d.department = %s OR d.ao_id = %s 
        ORDER BY d.uploaded_at DESC
    """, (session['user_department'], session['user_id']))
    documents = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('hod/ao/documents.html', documents=documents)

# Download Document Route
@ao_bp.route('/download-document/<document_id>')
def download_document(document_id):
    if session.get('user_role') != 'ao':
        return redirect('/hod/ao/login')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM ao_documents WHERE document_id = %s AND (department = %s OR ao_id = %s)", 
                  (document_id, session['user_department'], session['user_id']))
    document = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if document:
        return send_file(document['file_path'], as_attachment=True, download_name=document['original_filename'])
    else:
        flash('Document not found or access denied', 'error')
        return redirect('/hod/ao/documents')

# AO Logout Route
@ao_bp.route('/logout')
def ao_logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/hod/ao/login')