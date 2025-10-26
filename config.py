import mysql.connector

class Config:
    SECRET_KEY = 'cretcom-principal-2024'
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root', 
        'password': 'vnsvb',
        'database': 'attendrix'
    }

def get_db_connection():
    return mysql.connector.connect(**Config.DB_CONFIG)