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

const AdministrationDashboard = ({ user, onLogout, students = [], onAddStudent, onDeleteStudent, onChangePassword }: any) => {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [showAddStudent, setShowAddStudent] = useState(false);
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [changePasswordModal, setChangePasswordModal] = useState(false);
  
  const [filters, setFilters] = useState({
    department: '',
    batch: '',
    year: '',
    searchQuery: ''
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [newStudent, setNewStudent] = useState({
    roll_no: '',
    name: '',
    mobile: '',
    email: '',
    department: 'Computer Science',
    batch: '2023',
    current_year: '1st Year',
    aadhar_number: '',
    father_name: '',
    mother_name: '',
    guardian_mobile: '',
    address: ''
  });

  const departments = ['Computer Science', 'Electronics', 'Mechanical', 'Civil', 'Electrical'];
  const batches = ['2020', '2021', '2022', '2023', '2024'];
  const years = ['1st Year', '2nd Year', '3rd Year', '4th Year'];

  // Default delete function if not provided
  const defaultDeleteStudent = async (studentId: string) => {
    Alert.alert('Success', `Student ${studentId} deleted successfully`);
    return true;
  };

  // Default change password function if not provided
  const defaultChangePassword = async (currentPassword: string, newPassword: string) => {
    Alert.alert('Success', 'Password changed successfully');
    return true;
  };

  const filteredStudents = students.filter((student: any) => {
    const matchesDepartment = !filters.department || student.department === filters.department;
    const matchesBatch = !filters.batch || student.batch === filters.batch;
    const matchesYear = !filters.year || student.current_year === filters.year;
    const matchesSearch = !filters.searchQuery || 
      student.name.toLowerCase().includes(filters.searchQuery.toLowerCase()) ||
      student.roll_no.toLowerCase().includes(filters.searchQuery.toLowerCase()) ||
      student.mobile.includes(filters.searchQuery);

    return matchesDepartment && matchesBatch && matchesYear && matchesSearch;
  });

  const getDepartmentStats = () => {
    const stats: any = {};
    departments.forEach(dept => {
      stats[dept] = students.filter((student: any) => student.department === dept).length;
    });
    return stats;
  };

  const departmentStats = getDepartmentStats();

  const handleAddStudent = async () => {
    if (!newStudent.roll_no || !newStudent.name || !newStudent.mobile || !newStudent.department) {
      Alert.alert('Error', 'Please fill all required fields (Roll No, Name, Mobile, Department)');
      return;
    }

    if (!/^\d{10}$/.test(newStudent.mobile)) {
      Alert.alert('Error', 'Please enter a valid 10-digit mobile number');
      return;
    }

    if (newStudent.aadhar_number && !/^\d{12}$/.test(newStudent.aadhar_number)) {
      Alert.alert('Error', 'Please enter a valid 12-digit Aadhar number');
      return;
    }

    if (newStudent.guardian_mobile && !/^\d{10}$/.test(newStudent.guardian_mobile)) {
      Alert.alert('Error', 'Please enter a valid 10-digit guardian mobile number');
      return;
    }

    const studentData = {
      roll_no: newStudent.roll_no.trim(),
      name: newStudent.name.trim(),
      mobile: newStudent.mobile.trim(),
      email: newStudent.email.trim(),
      department: newStudent.department,
      batch: newStudent.batch,
      current_year: newStudent.current_year,
      aadhar_number: newStudent.aadhar_number.trim(),
      father_name: newStudent.father_name.trim(),
      mother_name: newStudent.mother_name.trim(),
      guardian_mobile: newStudent.guardian_mobile.trim(),
      address: newStudent.address.trim()
    };

    if (onAddStudent) {
      const success = await onAddStudent(studentData);
      if (success) {
        setShowAddStudent(false);
        setNewStudent({
          roll_no: '', name: '', mobile: '', email: '', department: 'Computer Science',
          batch: '2023', current_year: '1st Year', aadhar_number: '', father_name: '',
          mother_name: '', guardian_mobile: '', address: ''
        });
        Alert.alert('Success', 'Student added successfully!');
      }
    } else {
      Alert.alert('Success', 'Student added successfully (demo mode)');
      setShowAddStudent(false);
      setNewStudent({
        roll_no: '', name: '', mobile: '', email: '', department: 'Computer Science',
        batch: '2023', current_year: '1st Year', aadhar_number: '', father_name: '',
        mother_name: '', guardian_mobile: '', address: ''
      });
    }
  };

  const handleDeleteStudent = async () => {
    if (selectedStudent) {
      const deleteFunction = onDeleteStudent || defaultDeleteStudent;
      const success = await deleteFunction(selectedStudent.id);
      if (success) {
        setDeleteModalVisible(false);
        setSelectedStudent(null);
        Alert.alert('Success', 'Student deleted successfully');
      }
    }
  };

  const handleChangePassword = async () => {
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      Alert.alert('Error', 'Please fill all password fields');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      Alert.alert('Error', 'New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      Alert.alert('Error', 'New password must be at least 6 characters long');
      return;
    }

    const changePasswordFunction = onChangePassword || defaultChangePassword;
    const success = await changePasswordFunction(passwordData.currentPassword, passwordData.newPassword);
    if (success) {
      setChangePasswordModal(false);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      Alert.alert('Success', 'Password changed successfully');
    }
  };

  const confirmDelete = (student: any) => {
    setSelectedStudent(student);
    setDeleteModalVisible(true);
  };

  const clearFilters = () => {
    setFilters({
      department: '',
      batch: '',
      year: '',
      searchQuery: ''
    });
  };

  const renderDashboard = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Administration Dashboard</Text>
      <Text style={styles.welcomeText}>Welcome, {user?.name}!</Text>
      <Text style={styles.roleText}>Administration Officer - Student Management</Text>
      
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{students.length}</Text>
          <Text style={styles.statLabel}>Total Students</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{departments.length}</Text>
          <Text style={styles.statLabel}>Departments</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Department-wise Student Count</Text>
      <View style={styles.departmentStats}>
        {departments.map(dept => (
          <View key={dept} style={styles.departmentStatCard}>
            <Text style={styles.departmentName}>{dept}</Text>
            <Text style={styles.departmentCount}>{departmentStats[dept]}</Text>
          </View>
        ))}
      </View>

      <View style={styles.actionButtons}>
        <TouchableOpacity style={styles.mainActionButton} onPress={() => setShowAddStudent(true)}>
          <Text style={styles.mainActionButtonText}>🎓 Add New Student</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.passwordButton} onPress={() => setChangePasswordModal(true)}>
          <Text style={styles.passwordButtonText}>🔐 Change Password</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderStudents = () => (
    <View style={styles.tabContent}>
      <View style={styles.headerRow}>
        <Text style={styles.tabTitle}>Student Management</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.filterButton} onPress={() => setFilterModalVisible(true)}>
            <Text style={styles.filterButtonText}>🔍 Filter</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.addButton} onPress={() => setShowAddStudent(true)}>
            <Text style={styles.addButtonText}>🎓 Add Student</Text>
          </TouchableOpacity>
        </View>
      </View>

      {(filters.department || filters.batch || filters.year || filters.searchQuery) && (
        <View style={styles.activeFiltersContainer}>
          <Text style={styles.activeFiltersTitle}>Active Filters:</Text>
          <View style={styles.activeFilters}>
            {filters.department && (
              <View style={styles.activeFilterTag}>
                <Text style={styles.activeFilterText}>Dept: {filters.department}</Text>
              </View>
            )}
            {filters.batch && (
              <View style={styles.activeFilterTag}>
                <Text style={styles.activeFilterText}>Batch: {filters.batch}</Text>
              </View>
            )}
            {filters.year && (
              <View style={styles.activeFilterTag}>
                <Text style={styles.activeFilterText}>Year: {filters.year}</Text>
              </View>
            )}
            {filters.searchQuery && (
              <View style={styles.activeFilterTag}>
                <Text style={styles.activeFilterText}>Search: {filters.searchQuery}</Text>
              </View>
            )}
            <TouchableOpacity style={styles.clearFiltersButton} onPress={clearFilters}>
              <Text style={styles.clearFiltersText}>Clear All</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <Text style={styles.resultsCount}>
        Showing {filteredStudents.length} of {students.length} students
      </Text>

      <FlatList
        data={filteredStudents}
        keyExtractor={(item) => item.id?.toString() || Math.random().toString()}
        renderItem={({ item }) => (
          <View style={styles.studentCard}>
            <View style={styles.studentInfo}>
              <View style={styles.studentHeader}>
                <Text style={styles.studentName}>{item.name}</Text>
                <TouchableOpacity 
                  style={styles.deleteButton}
                  onPress={() => confirmDelete(item)}
                >
                  <Text style={styles.deleteButtonText}>🗑️</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.studentId}>Roll No: {item.roll_no}</Text>
              <Text style={styles.studentDetail}>📱 Mobile: {item.mobile}</Text>
              <Text style={styles.studentDetail}>📧 Email: {item.email || 'Not provided'}</Text>
              <Text style={styles.studentDetail}>🏫 Department: {item.department}</Text>
              <Text style={styles.studentDetail}>📅 Batch: {item.batch} • Year: {item.current_year}</Text>
              {item.aadhar_number && <Text style={styles.studentDetail}>🆔 Aadhar: {item.aadhar_number}</Text>}
              {item.father_name && <Text style={styles.studentDetail}>👨 Father: {item.father_name}</Text>}
              {item.guardian_mobile && <Text style={styles.studentDetail}>📞 Guardian: {item.guardian_mobile}</Text>}
              {item.address && <Text style={styles.studentAddress}>🏠 Address: {item.address}</Text>}
            </View>
          </View>
        )}
        contentContainerStyle={styles.flatListContent}
      />
    </View>
  );

  const renderFilterModal = () => (
    <Modal visible={filterModalVisible} animationType="slide" transparent={true}>
      <View style={styles.filterModalContainer}>
        <View style={styles.filterModalContent}>
          <Text style={styles.filterModalTitle}>Filter Students</Text>
          
          <Text style={styles.label}>Search</Text>
          <TextInput
            style={styles.input}
            placeholder="Search by name, roll no, or mobile"
            value={filters.searchQuery}
            onChangeText={(searchQuery) => setFilters(prev => ({ ...prev, searchQuery }))}
          />

          <Text style={styles.label}>Department</Text>
          <ScrollView horizontal style={styles.pickerContainer} showsHorizontalScrollIndicator={false}>
            <TouchableOpacity
              style={[styles.pickerOption, !filters.department && styles.selectedPicker]}
              onPress={() => setFilters(prev => ({ ...prev, department: '' }))}
            >
              <Text style={[styles.pickerText, !filters.department && styles.selectedPickerText]}>
                All Departments
              </Text>
            </TouchableOpacity>
            {departments.map(dept => (
              <TouchableOpacity
                key={dept}
                style={[styles.pickerOption, filters.department === dept && styles.selectedPicker]}
                onPress={() => setFilters(prev => ({ ...prev, department: dept }))}
              >
                <Text style={[styles.pickerText, filters.department === dept && styles.selectedPickerText]}>
                  {dept}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <Text style={styles.label}>Batch</Text>
          <ScrollView horizontal style={styles.pickerContainer} showsHorizontalScrollIndicator={false}>
            <TouchableOpacity
              style={[styles.pickerOption, !filters.batch && styles.selectedPicker]}
              onPress={() => setFilters(prev => ({ ...prev, batch: '' }))}
            >
              <Text style={[styles.pickerText, !filters.batch && styles.selectedPickerText]}>
                All Batches
              </Text>
            </TouchableOpacity>
            {batches.map(batch => (
              <TouchableOpacity
                key={batch}
                style={[styles.pickerOption, filters.batch === batch && styles.selectedPicker]}
                onPress={() => setFilters(prev => ({ ...prev, batch }))}
              >
                <Text style={[styles.pickerText, filters.batch === batch && styles.selectedPickerText]}>
                  {batch}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <Text style={styles.label}>Current Year</Text>
          <ScrollView horizontal style={styles.pickerContainer} showsHorizontalScrollIndicator={false}>
            <TouchableOpacity
              style={[styles.pickerOption, !filters.year && styles.selectedPicker]}
              onPress={() => setFilters(prev => ({ ...prev, year: '' }))}
            >
              <Text style={[styles.pickerText, !filters.year && styles.selectedPickerText]}>
                All Years
              </Text>
            </TouchableOpacity>
            {years.map(year => (
              <TouchableOpacity
                key={year}
                style={[styles.pickerOption, filters.year === year && styles.selectedPicker]}
                onPress={() => setFilters(prev => ({ ...prev, year }))}
              >
                <Text style={[styles.pickerText, filters.year === year && styles.selectedPickerText]}>
                  {year}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <View style={styles.filterModalButtons}>
            <TouchableOpacity 
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setFilterModalVisible(false)}
            >
              <Text style={styles.buttonText}>Close</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.modalButton, styles.clearButton]}
              onPress={clearFilters}
            >
              <Text style={styles.buttonText}>Clear Filters</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  const renderDeleteConfirmationModal = () => (
    <Modal visible={deleteModalVisible} animationType="fade" transparent={true}>
      <View style={styles.deleteModalContainer}>
        <View style={styles.deleteModalContent}>
          <Text style={styles.deleteModalTitle}>Delete Student</Text>
          <Text style={styles.deleteModalText}>
            Are you sure you want to delete {selectedStudent?.name} (Roll No: {selectedStudent?.roll_no})?
          </Text>
          <Text style={styles.deleteWarningText}>This action cannot be undone.</Text>
          
          <View style={styles.deleteModalButtons}>
            <TouchableOpacity 
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setDeleteModalVisible(false)}
            >
              <Text style={styles.buttonText}>Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.modalButton, styles.deleteConfirmButton]}
              onPress={handleDeleteStudent}
            >
              <Text style={styles.buttonText}>Delete</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  const renderChangePasswordModal = () => (
    <Modal visible={changePasswordModal} animationType="slide" transparent={true}>
      <View style={styles.filterModalContainer}>
        <View style={styles.filterModalContent}>
          <Text style={styles.filterModalTitle}>Change Password</Text>
          
          <Text style={styles.label}>Current Password</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter current password"
            value={passwordData.currentPassword}
            onChangeText={(currentPassword) => setPasswordData(prev => ({ ...prev, currentPassword }))}
            secureTextEntry
          />

          <Text style={styles.label}>New Password</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter new password"
            value={passwordData.newPassword}
            onChangeText={(newPassword) => setPasswordData(prev => ({ ...prev, newPassword }))}
            secureTextEntry
          />

          <Text style={styles.label}>Confirm New Password</Text>
          <TextInput
            style={styles.input}
            placeholder="Confirm new password"
            value={passwordData.confirmPassword}
            onChangeText={(confirmPassword) => setPasswordData(prev => ({ ...prev, confirmPassword }))}
            secureTextEntry
          />

          <View style={styles.filterModalButtons}>
            <TouchableOpacity 
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => {
                setChangePasswordModal(false);
                setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
              }}
            >
              <Text style={styles.buttonText}>Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.modalButton, styles.saveButton]}
              onPress={handleChangePassword}
            >
              <Text style={styles.buttonText}>Change Password</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  const renderAddStudentModal = () => (
    <Modal visible={showAddStudent} animationType="slide">
      <SafeAreaView style={styles.modalContainer}>
        <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={true}>
          <Text style={styles.modalTitle}>Add New Student</Text>
          <Text style={styles.modalSubtitle}>Complete Student Information</Text>
          
          <Text style={styles.label}>🎓 Roll No *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter Roll Number"
            value={newStudent.roll_no}
            onChangeText={(roll_no) => setNewStudent(prev => ({ ...prev, roll_no }))}
          />
          
          <Text style={styles.label}>👤 Full Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter full name"
            value={newStudent.name}
            onChangeText={(name) => setNewStudent(prev => ({ ...prev, name }))}
          />
          
          <Text style={styles.label}>📱 Mobile Number *</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter 10-digit mobile number"
            value={newStudent.mobile}
            onChangeText={(mobile) => setNewStudent(prev => ({ ...prev, mobile }))}
            keyboardType="phone-pad"
            maxLength={10}
          />
          
          <Text style={styles.label}>📧 Email Address</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter email address"
            value={newStudent.email}
            onChangeText={(email) => setNewStudent(prev => ({ ...prev, email }))}
            keyboardType="email-address"
          />
          
          <Text style={styles.label}>🏫 Department *</Text>
          <ScrollView horizontal style={styles.pickerContainer} showsHorizontalScrollIndicator={false}>
            {departments.map(dept => (
              <TouchableOpacity
                key={dept}
                style={[styles.pickerOption, newStudent.department === dept && styles.selectedPicker]}
                onPress={() => setNewStudent(prev => ({ ...prev, department: dept }))}
              >
                <Text style={[styles.pickerText, newStudent.department === dept && styles.selectedPickerText]}>
                  {dept}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          
          <Text style={styles.label}>📅 Batch</Text>
          <ScrollView horizontal style={styles.pickerContainer} showsHorizontalScrollIndicator={false}>
            {batches.map(batch => (
              <TouchableOpacity
                key={batch}
                style={[styles.pickerOption, newStudent.batch === batch && styles.selectedPicker]}
                onPress={() => setNewStudent(prev => ({ ...prev, batch }))}
              >
                <Text style={[styles.pickerText, newStudent.batch === batch && styles.selectedPickerText]}>
                  {batch}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          
          <Text style={styles.label}>🎯 Current Year</Text>
          <ScrollView horizontal style={styles.pickerContainer} showsHorizontalScrollIndicator={false}>
            {years.map(year => (
              <TouchableOpacity
                key={year}
                style={[styles.pickerOption, newStudent.current_year === year && styles.selectedPicker]}
                onPress={() => setNewStudent(prev => ({ ...prev, current_year: year }))}
              >
                <Text style={[styles.pickerText, newStudent.current_year === year && styles.selectedPickerText]}>
                  {year}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          
          <Text style={styles.label}>🆔 Aadhar Number</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter 12-digit Aadhar number"
            value={newStudent.aadhar_number}
            onChangeText={(aadhar_number) => setNewStudent(prev => ({ ...prev, aadhar_number }))}
            keyboardType="number-pad"
            maxLength={12}
          />
          
          <Text style={styles.label}>👨 Father's Name</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter father's full name"
            value={newStudent.father_name}
            onChangeText={(father_name) => setNewStudent(prev => ({ ...prev, father_name }))}
          />
          
          <Text style={styles.label}>👩 Mother's Name</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter mother's full name"
            value={newStudent.mother_name}
            onChangeText={(mother_name) => setNewStudent(prev => ({ ...prev, mother_name }))}
          />
          
          <Text style={styles.label}>📞 Guardian Mobile</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter guardian mobile number"
            value={newStudent.guardian_mobile}
            onChangeText={(guardian_mobile) => setNewStudent(prev => ({ ...prev, guardian_mobile }))}
            keyboardType="phone-pad"
            maxLength={10}
          />
          
          <Text style={styles.label}>🏠 Complete Address</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Enter complete residential address"
            value={newStudent.address}
            onChangeText={(address) => setNewStudent(prev => ({ ...prev, address }))}
            multiline
            numberOfLines={4}
          />

          <View style={styles.modalButtons}>
            <TouchableOpacity 
              style={[styles.modalButton, styles.cancelButton]}
              onPress={() => setShowAddStudent(false)}
            >
              <Text style={styles.buttonText}>❌ Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.modalButton, styles.saveButton]}
              onPress={handleAddStudent}
            >
              <Text style={styles.buttonText}>✅ Save Student</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  const ADMIN_TABS = ['Dashboard', 'Students'];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Administration Dashboard</Text>
        <Text style={styles.headerSubtitle}>Student Management System • {user?.name}</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.passwordHeaderButton} onPress={() => setChangePasswordModal(true)}>
            <Text style={styles.passwordHeaderButtonText}>🔐</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
            <Text style={styles.logoutButtonText}>🚪 Logout</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView horizontal style={styles.tabContainer} showsHorizontalScrollIndicator={false}>
        {ADMIN_TABS.map(tab => (
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
      </ScrollView>

      <View style={styles.content}>
        {activeTab === 'Dashboard' && renderDashboard()}
        {activeTab === 'Students' && renderStudents()}
      </View>

      {renderAddStudentModal()}
      {renderFilterModal()}
      {renderDeleteConfirmationModal()}
      {renderChangePasswordModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#2c3e50', padding: 20, paddingTop: 60 },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: 'white' },
  headerSubtitle: { fontSize: 16, color: '#bdc3c7', marginTop: 5 },
  headerButtons: { position: 'absolute', right: 20, top: 60, flexDirection: 'row', alignItems: 'center' },
  passwordHeaderButton: { backgroundColor: '#3498db', padding: 10, borderRadius: 8, marginRight: 10 },
  passwordHeaderButtonText: { color: 'white', fontSize: 16 },
  logoutButton: { backgroundColor: '#e74c3c', padding: 10, borderRadius: 8 },
  logoutButtonText: { color: 'white', fontWeight: 'bold' },
  tabContainer: { backgroundColor: 'white', borderBottomWidth: 1, borderBottomColor: '#ddd', maxHeight: 50 },
  tab: { paddingHorizontal: 15, paddingVertical: 12, borderBottomWidth: 3, borderBottomColor: 'transparent' },
  activeTab: { borderBottomColor: '#3498db' },
  tabText: { fontSize: 14, color: '#7f8c8d', fontWeight: '600' },
  activeTabText: { color: '#3498db', fontWeight: 'bold' },
  content: { flex: 1, padding: 15 },
  tabContent: { flex: 1 },
  tabTitle: { fontSize: 22, fontWeight: 'bold', marginBottom: 10, color: '#2c3e50' },
  welcomeText: { fontSize: 18, color: '#3498db', marginBottom: 5, fontWeight: '600' },
  roleText: { fontSize: 14, color: '#7f8c8d', marginBottom: 20 },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
  statCard: { width: '48%', backgroundColor: 'white', padding: 20, borderRadius: 12, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  statNumber: { fontSize: 28, fontWeight: 'bold', color: '#3498db' },
  statLabel: { fontSize: 14, color: '#7f8c8d', marginTop: 5, textAlign: 'center' },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginTop: 20, marginBottom: 15, color: '#2c3e50' },
  departmentStats: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginBottom: 20 },
  departmentStatCard: { width: '48%', backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 10, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.1, shadowRadius: 3, elevation: 2 },
  departmentName: { fontSize: 12, color: '#7f8c8d', textAlign: 'center', marginBottom: 5 },
  departmentCount: { fontSize: 20, fontWeight: 'bold', color: '#27ae60' },
  actionButtons: { marginBottom: 20 },
  mainActionButton: { backgroundColor: '#27ae60', padding: 18, borderRadius: 12, alignItems: 'center', marginBottom: 10, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  mainActionButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  passwordButton: { backgroundColor: '#3498db', padding: 18, borderRadius: 12, alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  passwordButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 },
  headerActions: { flexDirection: 'row', alignItems: 'center' },
  filterButton: { backgroundColor: '#3498db', padding: 12, borderRadius: 8, marginRight: 10 },
  filterButtonText: { color: 'white', fontWeight: 'bold', fontSize: 14 },
  addButton: { backgroundColor: '#27ae60', padding: 12, borderRadius: 8 },
  addButtonText: { color: 'white', fontWeight: 'bold', fontSize: 14 },
  activeFiltersContainer: { backgroundColor: '#e8f4fd', padding: 15, borderRadius: 10, marginBottom: 15 },
  activeFiltersTitle: { fontSize: 14, fontWeight: 'bold', color: '#3498db', marginBottom: 8 },
  activeFilters: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center' },
  activeFilterTag: { backgroundColor: '#3498db', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 15, marginRight: 8, marginBottom: 5 },
  activeFilterText: { color: 'white', fontSize: 12, fontWeight: 'bold' },
  clearFiltersButton: { backgroundColor: '#e74c3c', paddingHorizontal: 12, paddingVertical: 5, borderRadius: 15 },
  clearFiltersText: { color: 'white', fontSize: 12, fontWeight: 'bold' },
  resultsCount: { fontSize: 14, color: '#7f8c8d', marginBottom: 10, fontStyle: 'italic' },
  studentCard: { backgroundColor: 'white', padding: 20, borderRadius: 12, marginBottom: 15, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3 },
  studentHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 5 },
  studentInfo: { flex: 1 },
  studentName: { fontSize: 18, fontWeight: 'bold', color: '#2c3e50', marginBottom: 5, flex: 1 },
  studentId: { fontSize: 16, color: '#3498db', marginBottom: 8, fontWeight: '600' },
  studentDetail: { fontSize: 14, color: '#7f8c8d', marginBottom: 3 },
  studentAddress: { fontSize: 13, color: '#95a5a6', marginTop: 5, fontStyle: 'italic' },
  deleteButton: { padding: 5 },
  deleteButtonText: { fontSize: 18, color: '#e74c3c' },
  flatListContent: { paddingBottom: 20 },
  modalContainer: { flex: 1, backgroundColor: 'white' },
  modalContent: { flex: 1, padding: 20 },
  modalTitle: { fontSize: 24, fontWeight: 'bold', marginBottom: 10, textAlign: 'center', color: '#2c3e50' },
  modalSubtitle: { fontSize: 16, color: '#7f8c8d', textAlign: 'center', marginBottom: 20 },
  filterModalContainer: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  filterModalContent: { backgroundColor: 'white', borderRadius: 15, padding: 20, maxHeight: '80%' },
  filterModalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 20, textAlign: 'center', color: '#2c3e50' },
  deleteModalContainer: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  deleteModalContent: { backgroundColor: 'white', borderRadius: 15, padding: 20 },
  deleteModalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 15, textAlign: 'center', color: '#e74c3c' },
  deleteModalText: { fontSize: 16, marginBottom: 10, textAlign: 'center', color: '#2c3e50' },
  deleteWarningText: { fontSize: 14, color: '#e74c3c', textAlign: 'center', marginBottom: 20, fontStyle: 'italic' },
  label: { fontSize: 16, fontWeight: '600', marginBottom: 8, color: '#2c3e50' },
  input: { backgroundColor: 'white', padding: 15, borderRadius: 10, borderWidth: 1, borderColor: '#ddd', fontSize: 16, marginBottom: 15 },
  textArea: { height: 100, textAlignVertical: 'top' },
  pickerContainer: { marginBottom: 15 },
  pickerOption: { padding: 12, borderWidth: 1, borderColor: '#ddd', borderRadius: 8, marginRight: 10, marginBottom: 5 },
  selectedPicker: { backgroundColor: '#3498db', borderColor: '#3498db' },
  pickerText: { fontSize: 14, color: '#2c3e50' },
  selectedPickerText: { color: 'white', fontWeight: 'bold' },
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 20, marginBottom: 30 },
  filterModalButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 20 },
  deleteModalButtons: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 20 },
  modalButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', marginHorizontal: 5 },
  cancelButton: { backgroundColor: '#95a5a6' },
  saveButton: { backgroundColor: '#3498db' },
  clearButton: { backgroundColor: '#f39c12' },
  deleteConfirmButton: { backgroundColor: '#e74c3c' },
  buttonText: { color: 'white', fontWeight: 'bold', fontSize: 16 },
});

export default AdministrationDashboard;