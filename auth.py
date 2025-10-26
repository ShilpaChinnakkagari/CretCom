from flask import Blueprint, render_template, request, session, flash, redirect, url_for
import json

auth_bp = Blueprint('auth', __name__)

def load_data(file_name):
    try:
        with open(f'data/{file_name}', 'r') as f:
            return json.load(f)
    except:
        return {}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_data('users.json')
        
        if username in users and users[username]['password'] == password:
            session['user_id'] = username
            session['user_role'] = users[username]['role']
            session['user_name'] = users[username]['name']
            flash('Login successful!', 'success')
            return redirect(url_for('principal.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))