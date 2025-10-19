import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';

const HODDashboard = ({ user, onLogout }: { user: any, onLogout: () => void }) => {
  const [activeTab, setActiveTab] = useState('Dashboard');

  const renderDashboard = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Department Summary - {user.department}</Text>
      
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>25</Text>
          <Text style={styles.statLabel}>Faculty</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>850</Text>
          <Text style={styles.statLabel}>Students</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>85%</Text>
          <Text style={styles.statLabel}>Attendance</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>12</Text>
          <Text style={styles.statLabel}>Pending Requests</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.actionButton} onPress={() => setActiveTab('Faculty')}>
            <Text style={styles.actionText}>Manage Faculty</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => setActiveTab('Students')}>
            <Text style={styles.actionText}>Manage Students</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => setActiveTab('Attendance')}>
            <Text style={styles.actionText}>Attendance</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => setActiveTab('Permissions')}>
            <Text style={styles.actionText}>Permissions</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  const renderFacultyManagement = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Faculty Management</Text>
      <Text style={styles.sectionText}>Add/Update/Delete faculty members</Text>
      <Text style={styles.sectionText}>Manage salary and salary receipts</Text>
    </View>
  );

  const renderStudentManagement = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Student Management</Text>
      <Text style={styles.sectionText}>Manage student records and information</Text>
    </View>
  );

  const renderAttendanceMapping = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Course & Attendance Mapping</Text>
      <Text style={styles.sectionText}>Map courses and track attendance</Text>
    </View>
  );

  const renderPermissionRequests = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Permission Requests</Text>
      <Text style={styles.sectionText}>Manage faculty and student permission requests</Text>
      <Text style={styles.subText}>Student transfer requests to other departments</Text>
    </View>
  );

  const renderManageAO = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Manage Administrative Officers</Text>
      <Text style={styles.sectionText}>Manage AO assignments and responsibilities</Text>
    </View>
  );

  const renderClassTeachers = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Class Teachers/Mentor Management</Text>
      <Text style={styles.sectionText}>Assign and manage class teachers/mentors</Text>
    </View>
  );

  const renderPlacement = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Placement & Activities</Text>
      <Text style={styles.sectionText}>Manage student placements and department activities</Text>
    </View>
  );

  const renderAbsenceRequests = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Absence Requests from VPs</Text>
      <Text style={styles.sectionText}>Manage PM absence requests from Vice Principals</Text>
    </View>
  );

  const renderFeedbacks = () => (
    <View style={styles.tabContent}>
      <Text style={styles.tabTitle}>Feedbacks</Text>
      <Text style={styles.sectionText}>View and manage department feedbacks</Text>
    </View>
  );

  const HOD_TABS = [
    'Dashboard', 'Faculty', 'Students', 'Attendance', 'Permissions', 
    'Manage AO', 'Class Teachers', 'Placement', 'Absence', 'Feedbacks'
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>HOD Dashboard</Text>
        <Text style={styles.headerSubtitle}>{user.department} • {user.name}</Text>
        <TouchableOpacity style={styles.logoutButton} onPress={onLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <ScrollView horizontal style={styles.tabContainer} showsHorizontalScrollIndicator={false}>
        {HOD_TABS.map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab.length > 10 ? tab.substring(0, 8) + '...' : tab}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView style={styles.content}>
        {activeTab === 'Dashboard' && renderDashboard()}
        {activeTab === 'Faculty' && renderFacultyManagement()}
        {activeTab === 'Students' && renderStudentManagement()}
        {activeTab === 'Attendance' && renderAttendanceMapping()}
        {activeTab === 'Permissions' && renderPermissionRequests()}
        {activeTab === 'Manage AO' && renderManageAO()}
        {activeTab === 'Class Teachers' && renderClassTeachers()}
        {activeTab === 'Placement' && renderPlacement()}
        {activeTab === 'Absence' && renderAbsenceRequests()}
        {activeTab === 'Feedbacks' && renderFeedbacks()}
      </ScrollView>
    </SafeAreaView>
  );
};

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
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#ddd',
  },
  tab: {
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
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
  tabContent: {
    padding: 15,
  },
  tabTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  statCard: {
    width: '48%',
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3498db',
  },
  statLabel: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 5,
  },
  section: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#2c3e50',
  },
  sectionText: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 5,
  },
  subText: {
    fontSize: 12,
    color: '#95a5a6',
    fontStyle: 'italic',
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionButton: {
    backgroundColor: '#3498db',
    padding: 12,
    borderRadius: 8,
    width: '48%',
    alignItems: 'center',
    marginBottom: 10,
  },
  actionText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 12,
    textAlign: 'center',
  },
});

export default HODDashboard;