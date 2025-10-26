import json
from datetime import datetime

def load_data(file_name):
    try:
        with open(f'data/{file_name}', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(file_name, data):
    with open(f'data/{file_name}', 'w') as f:
        json.dump(data, f, indent=4)

def get_pending_approvals():
    approvals = load_data('approvals.json')
    return approvals.get('pending', [])

def approve_request(request_id, approved_by):
    approvals = load_data('approvals.json')
    
    for i, approval in enumerate(approvals['pending']):
        if str(approval['id']) == str(request_id):
            # Update approval status
            approval['status'] = 'approved'
            approval['approved_by'] = approved_by
            approval['approved_date'] = datetime.now().isoformat()
            
            # Move to approved list
            approvals['approved'].append(approval)
            approvals['pending'].pop(i)
            
            save_data('approvals.json', approvals)
            
            # If it's a user creation approval, activate the user
            if approval['type'] == 'user_creation':
                users = load_data('users.json')
                if approval['username'] in users:
                    users[approval['username']]['status'] = 'active'
                    save_data('users.json', users)
            
            return {'success': True, 'message': 'Request approved successfully'}
    
    return {'success': False, 'message': 'Request not found'}

def reject_request(request_id, rejected_by, reason):
    approvals = load_data('approvals.json')
    
    for i, approval in enumerate(approvals['pending']):
        if str(approval['id']) == str(request_id):
            # Update approval status
            approval['status'] = 'rejected'
            approval['rejected_by'] = rejected_by
            approval['rejected_date'] = datetime.now().isoformat()
            approval['rejection_reason'] = reason
            
            # Move to rejected list
            approvals['rejected'].append(approval)
            approvals['pending'].pop(i)
            
            save_data('approvals.json', approvals)
            
            return {'success': True, 'message': 'Request rejected successfully'}
    
    return {'success': False, 'message': 'Request not found'}

def create_approval_request(approval_data):
    approvals = load_data('approvals.json')
    
    # Generate unique ID
    approval_id = len(approvals['pending']) + len(approvals['approved']) + len(approvals['rejected']) + 1
    
    approval_request = {
        'id': approval_id,
        'type': approval_data['type'],
        'title': approval_data['title'],
        'description': approval_data.get('description', ''),
        'created_by': approval_data['created_by'],
        'created_date': datetime.now().isoformat(),
        'status': 'pending',
        'data': approval_data.get('data', {})
    }
    
    approvals['pending'].append(approval_request)
    save_data('approvals.json', approvals)
    
    return approval_id