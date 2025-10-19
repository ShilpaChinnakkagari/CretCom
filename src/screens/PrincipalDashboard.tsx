import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
  Modal,
  Alert,
  FlatList,
  Dimensions
} from 'react-native';
import { supabase } from '../config/supabase';
import { User, Department, Stats } from '../types/types';

const { width } = Dimensions.get('window');

export default function PrincipalDashboard({ navigation }: any) {
  const [activeTab, setActiveTab] = useState('Overview');
  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [newUser, setNewUser] = useState({ id: '', name: '', role: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await loadUsers();
    await loadDepartments();
    await loadStats();
  };

  const loadUsers = async () => {
    const { data, error } = await supabase.from('users').select('*');
    if (!error && data) setUsers(data);
  };

  const loadDepartments = async () => {
    const { data, error } = await supabase.from('departments').select('*');
    if (!error && data) setDepartments(data);
  };

  const loadStats = async () => {
    const { data, error } = await supabase.from('stats').select('*');
    if (!error && data && data.length > 0) setStats(data[0]);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigation.navigate('Login');
  };

  const addUser = async () => {
    if (!newUser.id || !newUser.name || !newUser.role) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }

    const userData = {
      id: newUser.id,
      name: newUser.name,
      role: newUser.role,
      password: `${newUser.id}@1234`
    };

    const { error } = await supabase.from('users').insert([userData]);
    
    if (error) {
      Alert.alert('Error', 'Failed to add user');
    } else {
      await loadUsers();
      setShowUserModal(false);
      setNewUser({ id: '', name: '', role: '' });
      Alert.alert('Success', 'User added successfully');
    }
  };

  const renderOverview = () => (
    <View>
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.totalStudents || 0}</Text>
          <Text style={styles.statLabel}>Total Students</Text>
          <Text style={styles.statChange}>+12% from last year</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.placementRate || 0}%</Text>
          <Text style={styles.statLabel}>Placement Rate</Text>
          <Text style={styles.statChange}>2023-24 batch</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.totalFaculty || 0}</Text>
          <Text style={styles.statLabel}>Total Faculty</Text>
          <Text style={styles.statChange}>+5 this semester</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{stats?.feeCollection || '0Cr'}</Text>
          <Text style={styles.statLabel}>Fee Collection</Text>
          <Text style={styles.statChange}>This academic year</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Department-wise Students</Text>
        {departments.map(dept => (
          <View key={dept.id} style={styles.deptRow}>
            <Text style={styles.deptName}>{dept.name}</Text>
            <Text style={styles.deptCount}>{dept.students}</Text>
          </View>
        ))}
      </View>
    </View>
  );

  const renderUserManagement = () => (
    <View>
      <TouchableOpacity style={styles.addButton} onPress={() => setShowUserModal(true)}>
        <Text style={styles.addButtonText}>+ Add New User</Text>
      </TouchableOpacity>

      <FlatList
        data={users}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.userCard}>
            <Text style={styles.userId}>{item.id}</Text>
            <Text style={styles.userName}>{item.name}</Text>
            <Text style={styles.userRole}>{item.role}</Text>
          </View>
        )}
      />
    </View>
  );

  const renderDepartments = () => (
    <View>
      <Text style={styles.sectionTitle}>Manage Departments</Text>
      {departments.map(dept => (
        <View key={dept.id} style={styles.deptCard}>
          <Text style={styles.deptName}>{dept.name}</Text>
          <Text>HOD: {dept.hod}</Text>
          <Text>Faculty: {dept.faculty}</Text>
          <Text>Students: {dept.students}</Text>
          <Text style={styles.statusActive}>Status: {dept.status}</Text>
        </View>
      ))}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Principal Dashboard</Text>
        <Text style={styles.headerSubtitle}>Super Admin</Text>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.tabContainer}>
        {['Overview', 'Departments', 'User Management'].map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'Overview' && renderOverview()}
        {activeTab === 'Departments' && renderDepartments()}
        {activeTab === 'User Management' && renderUserManagement()}
      </ScrollView>

      <Modal visible={showUserModal} animationType="slide">
        <View style={styles.modalContainer}>
          <Text style={styles.modalTitle}>Add New User</Text>
          <TextInput
            style={styles.modalInput}
            placeholder="User ID"
            value={newUser.id}
            onChangeText={(text) => setNewUser(prev => ({ ...prev, id: text }))}
          />
          <TextInput
            style={styles.modalInput}
            placeholder="Name"
            value={newUser.name}
            onChangeText={(text) => setNewUser(prev => ({ ...prev, name: text }))}
          />
          <TextInput
            style={styles.modalInput}
            placeholder="Role"
            value={newUser.role}
            onChangeText={(text) => setNewUser(prev => ({ ...prev, role: text }))}
          />
          <View style={styles.modalButtons}>
            <TouchableOpacity style={styles.cancelButton} onPress={() => setShowUserModal(false)}>
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.saveButton} onPress={addUser}>
              <Text style={styles.saveButtonText}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2c3e50',
    padding: 20,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#bdc3c7',
    marginTop: 5,
  },
  logoutButton: {
    position: 'absolute',
    right: 20,
    top: 60,
    backgroundColor: '#e74c3c',
    padding: 8,
    borderRadius: 5,
  },
  logoutButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
  },
  tab: {
    flex: 1,
    padding: 15,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3498db',
  },
  tabText: {
    fontSize: 14,
    color: '#7f8c8d',
  },
  activeTabText: {
    color: '#3498db',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statCard: {
    width: (width - 40) / 2,
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  statLabel: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 5,
  },
  statChange: {
    fontSize: 12,
    color: '#27ae60',
    marginTop: 2,
  },
  section: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  deptRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#ecf0f1',
  },
  deptName: {
    fontSize: 16,
    color: '#34495e',
  },
  deptCount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#3498db',
  },
  deptCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  statusActive: {
    color: '#27ae60',
    fontWeight: 'bold',
  },
  addButton: {
    backgroundColor: '#27ae60',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },
  addButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  userCard: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  userId: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  userName: {
    fontSize: 14,
    color: '#34495e',
    marginTop: 2,
  },
  userRole: {
    fontSize: 12,
    color: '#7f8c8d',
    marginTop: 2,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    backgroundColor: 'white',
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
    textAlign: 'center',
    color: '#2c3e50',
  },
  modalInput: {
    backgroundColor: '#ecf0f1',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
    fontSize: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#95a5a6',
    padding: 15,
    borderRadius: 10,
    marginRight: 10,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  saveButton: {
    flex: 1,
    backgroundColor: '#3498db',
    padding: 15,
    borderRadius: 10,
    marginLeft: 10,
    alignItems: 'center',
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
});