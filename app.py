from flask import Flask, render_template, request, session, redirect, flash, jsonify
from principal.routes import principal_bp
from admin.routes import admin_bp
from config import get_db_connection

app = Flask(__name__)
app.secret_key = 'cretcom-college-erp-2024'

app.register_blueprint(principal_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s AND status = 'active'", (username,))
        user = cursor.fetchone()
        
        if user and user['password'] == password:
            session['user_id'] = user['username']
            session['user_role'] = user['role']
            session['user_name'] = user['name']
            
            # Check if password needs to be changed
            password_changed = user.get('password_changed', False)
            
            if not password_changed and user['role'] != 'principal':
                session['force_password_change'] = True
                cursor.close()
                conn.close()
                flash('Please change your default password for security', 'warning')
                return redirect('/change-password')
            
            flash('Login successful!', 'success')
            
            # REDIRECT BASED ON ROLE
            if user['role'] == 'principal':
                return redirect('/principal/dashboard')
            elif user['role'] in ['administration_admin', 'college_admin', 'fee_admin', 'placement_admin', 'exam_admin', 'library_admin']:
                return redirect('/admin/dashboard')
            else:
                flash('No dashboard available for your role', 'info')
                return redirect('/login')
        else:
            flash('Invalid username or password', 'error')
        
        cursor.close()
        conn.close()
    
    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session or not session.get('force_password_change'):
        return redirect('/login')
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('change_password.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update password and mark as changed
        cursor.execute(
            "UPDATE users SET password = %s, password_changed = TRUE WHERE username = %s",
            (new_password, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        session.pop('force_password_change', None)
        flash('Password changed successfully!', 'success')
        
        # Redirect to appropriate dashboard
        if session.get('user_role') == 'principal':
            return redirect('/principal/dashboard')
        else:
            return redirect('/admin/dashboard')
    
    return render_template('change_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True, port=5000)