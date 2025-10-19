import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  ScrollView
} from 'react-native';
import { supabase } from '../config/supabase';

export default function LoginScreen({ navigation }: any) {
  const [userID, setUserID] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    if (!userID || !password) {
      Alert.alert('Error', 'Please enter User ID and Password');
      return;
    }

    try {
      // Check user in database
      const { data: users, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userID)
        .eq('password', password)
        .single();

      if (error || !users) {
        Alert.alert('Error', 'Invalid User ID or Password');
        return;
      }

      // Store session
      await supabase.auth.setSession({
        access_token: 'mock_token',
        refresh_token: 'mock_refresh_token'
      });

      // Navigate based on role
      if (users.role === 'Principal') {
        navigation.navigate('PrincipalDashboard');
      } else {
        Alert.alert('Success', `Welcome ${users.role}`);
      }

    } catch (error) {
      Alert.alert('Error', 'Login failed');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.loginTitle}>College ERP System</Text>
        <Text style={styles.loginSubtitle}>Login to access your portal</Text>
        
        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>User ID</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. SA31XXXX ST31XXXX"
            value={userID}
            onChangeText={setUserID}
            placeholderTextColor="#999"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.inputLabel}>Password</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter your password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholderTextColor="#999"
          />
        </View>

        <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
          <Text style={styles.loginButtonText}>Login</Text>
        </TouchableOpacity>

        <Text style={styles.forgotPassword}>Forgot Password?</Text>

        <View style={styles.demoContainer}>
          <Text style={styles.demoTitle}>Demo User IDs:</Text>
          <Text style={styles.demoText}>SA31ADMIN - Principal</Text>
          <Text style={styles.demoText}>FA31001 - Fee Admin</Text>
          <Text style={styles.demoText}>ST31001 - Student</Text>
          <Text style={styles.demoText}>DEPT31CSE - HOD</Text>
          <Text style={styles.demoText}>FC31001 - Faculty</Text>
          <Text style={styles.demoText}>PL31001 - Placement</Text>
          <Text style={styles.demoText}>VP31001 - Vice Principal</Text>
          <Text style={styles.demoNote}>Default passwords: Check role prefix + @1234</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContainer: {
    flexGrow: 1,
    padding: 20,
    justifyContent: 'center',
  },
  loginTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
    color: '#2c3e50',
  },
  loginSubtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 40,
    color: '#7f8c8d',
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#2c3e50',
  },
  input: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ddd',
    fontSize: 16,
  },
  loginButton: {
    backgroundColor: '#3498db',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 10,
  },
  loginButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  forgotPassword: {
    textAlign: 'center',
    marginTop: 15,
    color: '#3498db',
    fontSize: 14,
  },
  demoContainer: {
    marginTop: 40,
    padding: 20,
    backgroundColor: '#ecf0f1',
    borderRadius: 10,
  },
  demoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#2c3e50',
  },
  demoText: {
    fontSize: 14,
    marginBottom: 5,
    color: '#34495e',
  },
  demoNote: {
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 10,
    color: '#7f8c8d',
  },
});