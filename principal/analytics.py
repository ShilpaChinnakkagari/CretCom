import json
from datetime import datetime, timedelta

def load_data(file_name):
    try:
        with open(f'data/{file_name}', 'r') as f:
            return json.load(f)
    except:
        return {}

def get_system_stats():
    users = load_data('users.json')
    departments = load_data('departments.json')
    attendance = load_data('attendance.json')
    
    # User statistics
    user_stats = {
        'total_users': len(users),
        'principals': sum(1 for u in users.values() if u.get('role') == 'principal'),
        'vice_principals': sum(1 for u in users.values() if u.get('role') == 'vice_principal'),
        'hods': sum(1 for u in users.values() if u.get('role') == 'hod'),
        'faculty': sum(1 for u in users.values() if u.get('role') == 'faculty'),
        'students': sum(1 for u in users.values() if u.get('role') == 'student'),
        'admins': sum(1 for u in users.values() if any(admin in u.get('role', '') for admin in ['fee_admin', 'exam_admin', 'placement_admin']))
    }
    
    # Department statistics
    dept_stats = {
        'total_departments': len(departments),
        'departments_with_hod': sum(1 for dept in departments.values() if dept.get('hod')),
        'total_faculty': sum(dept.get('faculty_count', 0) for dept in departments.values()),
        'total_students': sum(dept.get('student_count', 0) for dept in departments.values())
    }
    
    # Attendance statistics (last 30 days)
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    recent_attendance = []
    for record in attendance.values():
        record_date = datetime.fromisoformat(record.get('date', '')).date()
        if record_date >= thirty_days_ago:
            recent_attendance.append(record)
    
    attendance_stats = {
        'total_records': len(recent_attendance),
        'present_count': sum(1 for r in recent_attendance if r.get('status') == 'Present'),
        'absent_count': sum(1 for r in recent_attendance if r.get('status') == 'Absent'),
        'attendance_rate': round((sum(1 for r in recent_attendance if r.get('status') == 'Present') / len(recent_attendance)) * 100, 2) if recent_attendance else 0
    }
    
    return {
        'user_stats': user_stats,
        'dept_stats': dept_stats,
        'attendance_stats': attendance_stats,
        'last_updated': datetime.now().isoformat()
    }

def get_department_stats():
    departments = load_data('departments.json')
    users = load_data('users.json')
    attendance = load_data('attendance.json')
    
    dept_stats = {}
    
    for dept_name, dept_data in departments.items():
        # Count faculty in this department
        faculty_count = sum(1 for u in users.values() if u.get('department') == dept_name and u.get('role') == 'faculty')
        
        # Count students in this department
        student_count = sum(1 for u in users.values() if u.get('department') == dept_name and u.get('role') == 'student')
        
        # Calculate attendance rate for this department
        dept_attendance = [r for r in attendance.values() if any(
            u for u in users.values() 
            if u.get('username') == r.get('student_id') and u.get('department') == dept_name
        )]
        
        present_count = sum(1 for r in dept_attendance if r.get('status') == 'Present')
        attendance_rate = round((present_count / len(dept_attendance)) * 100, 2) if dept_attendance else 0
        
        dept_stats[dept_name] = {
            'hod': dept_data.get('hod', 'Not Assigned'),
            'faculty_count': faculty_count,
            'student_count': student_count,
            'attendance_rate': attendance_rate,
            'total_users': faculty_count + student_count
        }
    
    return dept_stats

def get_recent_activity():
    approvals = load_data('approvals.json')
    users = load_data('users.json')
    
    recent_activity = []
    
    # Get recent approvals (last 10)
    recent_approvals = approvals.get('approved', [])[-10:] + approvals.get('rejected', [])[-10:]
    recent_approvals.sort(key=lambda x: x.get('approved_date') or x.get('rejected_date') or x.get('created_date'), reverse=True)
    
    for approval in recent_approvals[:10]:
        activity = {
            'type': 'approval',
            'title': approval.get('title', ''),
            'status': approval.get('status', ''),
            'date': approval.get('approved_date') or approval.get('rejected_date') or approval.get('created_date'),
            'user': approval.get('approved_by') or approval.get('rejected_by') or approval.get('created_by')
        }
        recent_activity.append(activity)
    
    return recent_activity[:10]  # Return only 10 most recent