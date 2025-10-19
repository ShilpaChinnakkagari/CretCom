import * as SQLite from 'expo-sqlite';

const db = SQLite.openDatabase('collegeerp.db');

export const initDatabase = () => {
  return new Promise((resolve, reject) => {
    db.transaction(tx => {
      // Users table
      tx.executeSql(
        `CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL,
          name TEXT NOT NULL,
          role TEXT NOT NULL,
          department TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );`,
        [],
        () => console.log('Users table ready'),
        (_, error) => {
          console.log('Users table error:', error);
          return true;
        }
      );

      // Students table
      tx.executeSql(
        `CREATE TABLE IF NOT EXISTS students (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          roll_no TEXT UNIQUE NOT NULL,
          name TEXT NOT NULL,
          mobile TEXT NOT NULL,
          email TEXT,
          department TEXT NOT NULL,
          batch TEXT NOT NULL,
          current_year TEXT NOT NULL,
          aadhar_number TEXT,
          father_name TEXT,
          mother_name TEXT,
          guardian_mobile TEXT,
          address TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          created_by TEXT NOT NULL
        );`,
        [],
        () => console.log('Students table ready'),
        (_, error) => {
          console.log('Students table error:', error);
          return true;
        }
      );

      // Insert demo users
      tx.executeSql(
        `INSERT OR IGNORE INTO users (username, password, name, role, department) VALUES 
        ('principal', 'principal123', 'Dr. Principal', 'principal', NULL),
        ('admin', 'admin123', 'Admin Officer', 'administration', NULL),
        ('hod_cs', 'hod123', 'HOD Computer Science', 'hod', 'Computer Science')`,
        [],
        () => {
          console.log('Demo users inserted');
          resolve(true);
        },
        (_, error) => {
          console.log('Demo users error:', error);
          resolve(true); // Still resolve even if demo users exist
          return true;
        }
      );
    });
  });
};

export const getUserByCredentials = (username: string, password: string): Promise<any> => {
  return new Promise((resolve, reject) => {
    db.transaction(tx => {
      tx.executeSql(
        'SELECT * FROM users WHERE username = ? AND password = ?',
        [username, password],
        (_, { rows }) => {
          resolve(rows._array[0] || null);
        },
        (_, error) => {
          reject(error);
          return true;
        }
      );
    });
  });
};

export const getAllUsers = (): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    db.transaction(tx => {
      tx.executeSql(
        'SELECT * FROM users ORDER BY created_at DESC',
        [],
        (_, { rows }) => resolve(rows._array),
        (_, error) => {
          reject(error);
          return true;
        }
      );
    });
  });
};

export const addUser = (userData: any): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    db.transaction(tx => {
      tx.executeSql(
        `INSERT INTO users (username, password, name, role, department) VALUES (?, ?, ?, ?, ?)`,
        [userData.username, userData.password, userData.name, userData.role, userData.department || null],
        () => resolve(true),
        (_, error) => {
          reject(error);
          return true;
        }
      );
    });
  });
};

export const getAllStudents = (): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    db.transaction(tx => {
      tx.executeSql(
        'SELECT * FROM students ORDER BY created_at DESC',
        [],
        (_, { rows }) => resolve(rows._array),
        (_, error) => {
          reject(error);
          return true;
        }
      );
    });
  });
};

export const addStudent = (studentData: any): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    db.transaction(tx => {
      tx.executeSql(
        `INSERT INTO students (roll_no, name, mobile, email, department, batch, current_year, aadhar_number, father_name, mother_name, guardian_mobile, address, created_by) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          studentData.roll_no, studentData.name, studentData.mobile, studentData.email,
          studentData.department, studentData.batch, studentData.current_year,
          studentData.aadhar_number, studentData.father_name, studentData.mother_name,
          studentData.guardian_mobile, studentData.address, studentData.created_by
        ],
        () => resolve(true),
        (_, error) => {
          reject(error);
          return true;
        }
      );
    });
  });
};