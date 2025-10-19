import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
  Alert,
  Modal,
  FlatList,
} from 'react-native';

const PrincipalDashboard = ({ user, onLogout, users, onAddUser, students }: any) => {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    name: '',
    role: 'administration',
    department: ''
  });

  const handleAddUser = async () => {
    if (!newUser.username || !newUser.password || !newUser.name || !newUser.role) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    const existingUser = users.find((u: any) => u.username === newUser.username);
    if (existingUser) {
      Alert.alert('Error', 'Username already exists!');
      return;
    }

    const userData = {
      username: newUser.username.trim(),
      password: newUser.password.trim(),
      name: newUser.name.trim(),
      role: newUser.role as 'principal' | 'administration' | 'hod',
      department: newUser.department?.trim() || undefined
    };

    const success = await onAddUser(userData);
    
    if (success) {
      setNewUser({
        username: '',
        password: '',
        name: '',
        role: 'administration',
        department: ''
      });
      setShowAddUser(false);
    }
  };

  const renderDashboard = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Principal Dashboard</Text>
      <Text style={styles.welcomeText}>Welcome, {user.name}!</Text>
      
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{users.length}</Text>
          <Text style={styles.statLabel}>Total Users</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{students.length}</Text>
          <Text style={styles.statLabel}>Total Students</Text>
        </View>
      </View>

      <TouchableOpacity style={styles.mainActionButton} onPress={() => setShowAddUser(true)}>
        <Text style={styles.mainActionButtonText}>👥 Add New User</Text>
      </TouchableOpacity>
    </View>
  );

  const renderUserManagement = () => (
    <View style={styles.tabContent}>
      <View style={styles.headerRow}>
        <Text style={styles.tabTitle}>User Management</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => setShowAddUser(true)}>
          <Text style={styles.addButtonText}>👥 Add User</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={users}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.userCard}>
            <Text style={styles.userName}>{item.name}</Text>
            <Text style={styles.userDetail}>Username: {item.username}</Text>
            <Text style={styles.userDetail}>Role: {item.role}</Text>
            {item.department && <Text style={styles.userDetail}>Department: {item.department}</Text>}
          </View>
        )}
        contentContainerStyle={styles.flatListContent}
      />
    </View>
  );

  const renderAddUserModal = () => (
    <Modal visible={showAddUser} animationType="slide">
      <SafeAreaView style={styles.modalContainer}>
        <ScrollView style={styles.modalContent}>
          <Text style={styles.modalTitle}>Add New User</Text>
          
          <Text style={styles.label}>👤 Username *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter username"
            value={newUser.username}
            onChangeText={(username) => setNewUser(prev => ({ ...prev, username }))}
            autoCapitalize="none"
          />
          
          <Text style={styles.label}>🔑 Password *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter password"
            value={newUser.password}
            onChangeText={(password) => setNewUser(prev => ({ ...prev, password }))}
            secureTextEntry
          />
          
          <Text style={styles.label}>📛 Full Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter full name"
            value={newUser.name}
            onChangeText={(name) => setNewUser(prev => ({ ...prev, name }))}
          />
          
          <Text style={styles.label}>🎯 Role *</Text>
          <View style={styles.roleOptions}>
            <TouchableOpacity
              style={[styles.roleButton, newUser.role === 'administration' && styles.selectedRole]}
              onPress={() => setNewUser(prev => ({ ...prev, role: 'administration' }))}
            >
              <Text style={[styles.roleText, newUser.role === 'administration' && styles.selectedRoleText]}>
                Administration
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.roleButton, newUser.role === 'hod' && styles.selectedRole]}
              onPress={() => setNewUser(prev => ({ ...prev, role: 'hod' }))}
            >
              <Text style={[styles.roleText, newUser.role === 'hod' && styles.selectedRoleText]}>
                HOD
              </Text>
            </TouchableOpacity>
          </View>
          
          {newUser.role === 'hod' && (
            <>
              <Text style={styles.label}>🏫 Department</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter department"
                value={newUser.department}
                onChangeText={(department) => setNewUser(prev => ({ ...prev, department }))}
              />
            </>
          )}

          <View style={styles.modalButtons}>
            <TouchableOpacity 
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setShowAddUser(false)}
            >
              <Text style={styles.buttonText}>❌ Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.modalButton, styles.saveButton]}
              onPress={handleAddUser}
            >
              <Text style={styles.buttonText}>✅ Save User</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  const TABS = ['Dashboard', 'UserManagement'];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Principal Dashboard</Text>
        <Text style={styles.headerSubtitle}>System Administration • {user.name}</Text>
        <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
          <Text style={styles.logoutButtonText}>🚪 Logout</Text>
        </TouchableOpacity>
      </View>

      <ScrollView horizontal style={styles.tabContainer}>
        {TABS.map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'UserManagement' ? 'User Management' : tab}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={styles.content}>
        {activeTab === 'Dashboard' && renderDashboard()}
        {activeTab === 'UserManagement' && renderUserManagement()}
      </View>

      {renderAddUserModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#2c3e50', padding: 20, paddingTop: 60 },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: 'white' },
  headerSubtitle: { fontSize: 16, color: '#bdc3c7', marginTop: 5 },
  logoutButton: { position: 'absolute', right: 20, top: 60, backgroundColor: '#e74c3c', padding: 10, borderRadius: 8 },
  logoutButtonText: { color: 'white', fontWeight: 'bold' },
  tabContainer: { backgroundColor: 'white', borderBottomWidth: 1, borderBottomColor: '#ddd' },
  tab: { paddingHorizontal: 15, paddingVertical: 12, borderBottomWidth: 3, borderBottomColor: 'transparent' },
  activeTab: { borderBottomColor: '#3498db' },
  tabText: { fontSize: 14, color: '#7f8c8d', fontWeight: '600' },
  activeTabText: { color: '#3498db', fontWeight: 'bold' },
  content: { flex: 1, padding: 15 },
  tabContent: { flex: 1 },
  tabTitle: { fontSize: 22, fontWeight: 'bold', marginBottom: 10, color: '#2c3e50' },
  welcomeText: { fontSize: 18, color: '#3498db', marginBottom: 5, fontWeight: '600' },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
  statCard: { width: '48%', backgroundColor: 'white', padding: 20, borderRadius: 12, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  statNumber: { fontSize: 28, fontWeight: 'bold', color: '#3498db' },
  statLabel: { fontSize: 14, color: '#7f8c8d', marginTop: 5, textAlign: 'center' },
  mainActionButton: { backgroundColor: '#27ae60', padding: 18, borderRadius: 12, alignItems: 'center', marginBottom: 20, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  mainActionButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 },
  addButton: { backgroundColor: '#27ae60', padding: 12, borderRadius: 8 },
  addButtonText: { color: 'white', fontWeight: 'bold', fontSize: 14 },
  userCard: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginBottom: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  userName: { fontSize: 18, fontWeight: 'bold', color: '#2c3e50', marginBottom: 5 },
  userDetail: { fontSize: 14, color: '#7f8c8d', marginBottom: 3 },
  flatListContent: { paddingBottom: 20 },
  modalContainer: { flex: 1, backgroundColor: 'white' },
  modalContent: { flex: 1, padding: 20 },
  modalTitle: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center', color: '#2c3e50' },
  label: { fontSize: 16, fontWeight: '600', marginBottom: 8, color: '#2c3e50' },
  input: { backgroundColor: 'white', padding: 15, borderRadius: 10, borderWidth: 1, borderColor: '#ddd', fontSize: 16, marginBottom: 15 },
  roleOptions: { flexDirection: 'row', marginBottom: 15 },
  roleButton: { flex: 1, padding: 12, borderWidth: 1, borderColor: '#ddd', borderRadius: 8, marginHorizontal: 5, alignItems: 'center' },
  selectedRole: { backgroundColor: '#3498db', borderColor: '#3498db' },
  roleText: { fontSize: 14, color: '#2c3e50' },
  selectedRoleText: { color: 'white', fontWeight: 'bold' },
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 20 },
  modalButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', marginHorizontal: 5 },
  cancelButton: { backgroundColor: '#95a5a6' },
  saveButton: { backgroundColor: '#3498db' },
  buttonText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
});

export default PrincipalDashboard;