import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { initDatabase, getUserByCredentials, getAllUsers, addUser, getAllStudents, addStudent } from './database';

// Login Screen
const LoginScreen = ({ onLogin, loading }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = () => {
    if (username && password) {
      onLogin(username, password);
    } else {
      Alert.alert('Error', 'Please enter both username and password');
    }
  };

  return (
    <SafeAreaView style={styles.loginContainer}>
      <View style={styles.loginHeader}>
        <Text style={styles.loginTitle}>COLLEGE ERP SYSTEM</Text>
        <Text style={styles.loginSubtitle}>Login to Continue</Text>
      </View>

      <View style={styles.loginForm}>
        <TextInput
          style={styles.input}
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        
        <TouchableOpacity style={styles.loginButton} onPress={handleLogin} disabled={loading}>
          {loading ? <ActivityIndicator color="white" /> : <Text style={styles.loginButtonText}>🚪 Login</Text>}
        </TouchableOpacity>

        <View style={styles.demoAccounts}>
          <Text style={styles.demoTitle}>Demo Accounts:</Text>
          <Text style={styles.demoAccount}>Principal: principal / principal123</Text>
          <Text style={styles.demoAccount}>Admin: admin / admin123</Text>
          <Text style={styles.demoAccount}>HOD CS: hod_cs / hod123</Text>
        </View>
      </View>
    </SafeAreaView>
  );
};

// Import your components
import PrincipalDashboard from './PrincipalDashboard';
import AdministrationDashboard from './AdministrationDashboard';
import HODDashboard from './HODDashboard';

const App = () => {
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      await initDatabase();
      const [usersData, studentsData] = await Promise.all([getAllUsers(), getAllStudents()]);
      setUsers(usersData);
      setStudents(studentsData);
      setAppReady(true);
    } catch (error) {
      console.error('App initialization error:', error);
      Alert.alert('Error', 'Failed to initialize app');
      setAppReady(true);
    }
  };

  const handleLogin = async (username: string, password: string) => {
    setLoading(true);
    try {
      const user = await getUserByCredentials(username, password);
      if (user) {
        setCurrentUser(user);
        Alert.alert('Success', `Welcome ${user.name}!`);
      } else {
        Alert.alert('Error', 'Invalid username or password');
      }
    } catch (error) {
      Alert.alert('Error', 'Login failed');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    Alert.alert('Logged Out', 'You have been successfully logged out');
  };

  const handleAddUser = async (userData) => {
    try {
      await addUser(userData);
      const updatedUsers = await getAllUsers();
      setUsers(updatedUsers);
      Alert.alert('Success', `User ${userData.name} created!`);
      return true;
    } catch (error) {
      Alert.alert('Error', 'Failed to create user');
      return false;
    }
  };

  const handleAddStudent = async (studentData) => {
    try {
      await addStudent({
        ...studentData,
        created_by: currentUser?.name || 'Administration'
      });
      const updatedStudents = await getAllStudents();
      setStudents(updatedStudents);
      Alert.alert('Success', `Student ${studentData.name} added!`);
      return true;
    } catch (error) {
      Alert.alert('Error', 'Failed to save student');
      return false;
    }
  };

  if (!appReady) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3498db" />
        <Text style={styles.loadingText}>Loading College ERP...</Text>
      </View>
    );
  }

  if (!currentUser) {
    return <LoginScreen onLogin={handleLogin} loading={loading} />;
  }

  switch (currentUser.role) {
    case 'principal':
      return <PrincipalDashboard user={currentUser} onLogout={handleLogout} users={users} onAddUser={handleAddUser} students={students} />;
    case 'administration':
      return <AdministrationDashboard user={currentUser} onLogout={handleLogout} students={students} onAddStudent={handleAddStudent} />;
    case 'hod':
      return <HODDashboard user={currentUser} onLogout={handleLogout} students={students.filter(s => s.department === currentUser.department)} />;
    default:
      return (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Unknown user role</Text>
          <TouchableOpacity style={styles.button} onPress={handleLogout}>
            <Text style={styles.buttonText}>Return to Login</Text>
          </TouchableOpacity>
        </View>
      );
  }
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#2c3e50' },
  loadingText: { color: 'white', fontSize: 18, marginTop: 20 },
  loginContainer: { flex: 1, backgroundColor: '#2c3e50', justifyContent: 'center', padding: 20 },
  loginHeader: { alignItems: 'center', marginBottom: 50 },
  loginTitle: { fontSize: 28, fontWeight: 'bold', color: 'white', marginBottom: 10 },
  loginSubtitle: { fontSize: 18, color: '#bdc3c7' },
  loginForm: { backgroundColor: 'white', padding: 30, borderRadius: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 8 },
  input: { backgroundColor: '#f8f9fa', padding: 15, borderRadius: 10, borderWidth: 1, borderColor: '#ddd', fontSize: 16, marginBottom: 20 },
  loginButton: { backgroundColor: '#3498db', padding: 18, borderRadius: 10, alignItems: 'center', marginBottom: 20 },
  loginButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  demoAccounts: { marginTop: 20, padding: 15, backgroundColor: '#f8f9fa', borderRadius: 10, borderLeftWidth: 4, borderLeftColor: '#3498db' },
  demoTitle: { fontSize: 16, fontWeight: 'bold', color: '#2c3e50', marginBottom: 10 },
  demoAccount: { fontSize: 14, color: '#7f8c8d', marginBottom: 5 },
  errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  errorText: { fontSize: 18, color: '#e74c3c', marginBottom: 20, textAlign: 'center' },
  button: { backgroundColor: '#3498db', padding: 15, borderRadius: 10, minWidth: 150, alignItems: 'center' },
  buttonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
});

export default App;