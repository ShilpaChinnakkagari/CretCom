import json

def load_data(file_name):
    try:
        with open(f'data/{file_name}', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(file_name, data):
    with open(f'data/{file_name}', 'w') as f:
        json.dump(data, f, indent=4)