import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, Alert, ScrollView } from 'react-native';

export default function App() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [token, setToken] = useState(null);
  const [userData, setUserData] = useState(null);
  const [history, setHistory] = useState(null);
  
  // App ki screen change karne ke liye state (dashboard ya createRide)
  const [currentScreen, setCurrentScreen] = useState('dashboard');

  // Nayi ride banane ke form ki states (Default Mumbai ke coordinates daale hain taaki baar baar type na karna pade)
  const [startLat, setStartLat] = useState('19.0760');
  const [startLng, setStartLng] = useState('72.8777');
  const [endLat, setEndLat] = useState('19.1136');
  const [endLng, setEndLng] = useState('72.8697');
  const [departureTime, setDepartureTime] = useState('2026-11-12T10:00:00');

  // Yahan apna asli IP address daalein
  const BACKEND_URL = '192.168.0.108:8000'; 

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please email aur password daalein.');
      return;
    }
    try {
      const response = await fetch(`${BACKEND_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
      });
      const data = await response.json();
      if (response.ok) {
        setToken(data.access_token);
        fetchMyProfile(data.access_token); 
        fetchMyHistory(data.access_token);
      } else {
        Alert.alert('Login Failed', data.detail || 'Galat details');
      }
    } catch (error) {
      Alert.alert('Network Error', 'Backend se connect nahi ho paya.');
    }
  };

  const fetchMyProfile = async (accessToken) => {
    try {
      const response = await fetch(`${BACKEND_URL}/me`, { headers: { 'Authorization': `Bearer ${accessToken}` } });
      if (response.ok) setUserData(await response.json());
    } catch (error) { console.log('Profile fetch error:', error); }
  };

  const fetchMyHistory = async (accessToken) => {
    try {
      const response = await fetch(`${BACKEND_URL}/users/me/history`, { headers: { 'Authorization': `Bearer ${accessToken}` } });
      if (response.ok) setHistory(await response.json());
    } catch (error) { console.log('History fetch error:', error); }
  };

  // NAYI RIDE BACKEND PAR BHEJNE KA FUNCTION
  const handleCreateRide = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/rides/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          start_lat: parseFloat(startLat),
          start_lng: parseFloat(startLng),
          end_lat: parseFloat(endLat),
          end_lng: parseFloat(endLng),
          departure_time: departureTime
        })
      });

      if (response.ok) {
        Alert.alert('Success! 🚀', 'Aapki ride live ho gayi hai!');
        setCurrentScreen('dashboard');
        fetchMyHistory(token); // History update karein
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.detail || 'Ride create nahi ho payi.');
      }
    } catch (error) {
      Alert.alert('Network Error', 'Ride backend tak nahi pohochi.');
    }
  };

  const handleLogout = () => {
    setToken(null);
    setUserData(null);
    setHistory(null);
    setEmail('');
    setPassword('');
    setCurrentScreen('dashboard');
  };

  // -----------------------------------------------------
  // SCREEN: CREATE RIDE FORM
  // -----------------------------------------------------
  if (token && currentScreen === 'createRide') {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Post a Ride 🏍️</Text>
        
        <View style={styles.card}>
          <Text style={styles.label}>Start Latitude</Text>
          <TextInput style={styles.input} value={startLat} onChangeText={setStartLat} keyboardType="numeric" />
          
          <Text style={styles.label}>Start Longitude</Text>
          <TextInput style={styles.input} value={startLng} onChangeText={setStartLng} keyboardType="numeric" />
          
          <Text style={styles.label}>End Latitude</Text>
          <TextInput style={styles.input} value={endLat} onChangeText={setEndLat} keyboardType="numeric" />
          
          <Text style={styles.label}>End Longitude</Text>
          <TextInput style={styles.input} value={endLng} onChangeText={setEndLng} keyboardType="numeric" />
          
          <Text style={styles.label}>Departure Time (YYYY-MM-DDTHH:MM:SS)</Text>
          <TextInput style={styles.input} value={departureTime} onChangeText={setDepartureTime} />
        </View>

        <TouchableOpacity style={styles.button} onPress={handleCreateRide}>
          <Text style={styles.buttonText}>Publish Ride</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.button, {backgroundColor: '#6c757d'}]} onPress={() => setCurrentScreen('dashboard')}>
          <Text style={styles.buttonText}>Cancel</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // -----------------------------------------------------
  // SCREEN: DASHBOARD
  // -----------------------------------------------------
  if (token && userData && currentScreen === 'dashboard') {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Dashboard</Text>
        
        <View style={styles.card}>
          <Text style={styles.welcomeText}>{userData.message}</Text>
          <Text style={styles.roleText}>Role: {userData.is_rider ? "🏍️ Bike Owner (Rider)" : "🎒 Commuter"}</Text>
        </View>

        {history && (
          <View style={styles.card}>
            <Text style={styles.statsTitle}>Aapki Ride History 📊</Text>
            <Text style={styles.statsText}>Rides Given: {history.total_rides_given}</Text>
            <Text style={styles.statsText}>Rides Taken: {history.total_rides_taken}</Text>
          </View>
        )}

        {/* Agar user Rider hai, toh hi usko yeh naya Create Ride button dikhega */}
        {userData.is_rider && (
          <TouchableOpacity style={[styles.button, {backgroundColor: '#28a745', marginBottom: 15}]} onPress={() => setCurrentScreen('createRide')}>
            <Text style={styles.buttonText}>🏍️ Create New Ride</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={[styles.button, {backgroundColor: '#FF3B30'}]} onPress={handleLogout}>
          <Text style={styles.buttonText}>Logout</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // -----------------------------------------------------
  // SCREEN: LOGIN
  // -----------------------------------------------------
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Bike Pooling</Text>
      <TextInput style={styles.input} placeholder="Email ID" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
      <TextInput style={styles.input} placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry />
      <TouchableOpacity style={styles.button} onPress={handleLogin}>
        <Text style={styles.buttonText}>Login</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, backgroundColor: '#f5f5f5', alignItems: 'center', justifyContent: 'center', padding: 20 },
  title: { fontSize: 32, fontWeight: 'bold', marginBottom: 30, color: '#333', marginTop: 40 },
  label: { fontSize: 14, fontWeight: 'bold', color: '#555', marginBottom: 5, alignSelf: 'flex-start' },
  input: { width: '100%', backgroundColor: 'white', padding: 12, borderRadius: 10, marginBottom: 15, borderWidth: 1, borderColor: '#ddd', fontSize: 16 },
  button: { width: '100%', backgroundColor: '#007BFF', padding: 15, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  buttonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  card: { backgroundColor: 'white', padding: 20, borderRadius: 10, width: '100%', marginBottom: 20, elevation: 3 },
  welcomeText: { fontSize: 18, color: '#333', marginBottom: 10 },
  roleText: { fontSize: 16, fontWeight: 'bold', color: '#007BFF' },
  statsTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 10, color: '#333' },
  statsText: { fontSize: 16, color: '#555', marginBottom: 5 }
});