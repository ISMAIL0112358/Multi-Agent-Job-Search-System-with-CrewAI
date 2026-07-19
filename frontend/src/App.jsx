import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import HRDashboardPage from './pages/HRDashboardPage';
import Loader from './components/Loader';
import client from './api/client';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loader message="Loading..." />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loader message="Loading..." />;
  if (user) return <Navigate to={user.role === 'hr' ? '/hr' : '/'} replace />;
  return children;
}

function App() {
  const [googleClientId, setGoogleClientId] = useState('');
  const [loadingConfig, setLoadingConfig] = useState(true);

  useEffect(() => {
    client.get('/auth/config')
      .then((res) => {
        setGoogleClientId(res.data.google_client_id || '');
      })
      .catch((err) => {
        console.error("Failed to load backend configuration:", err);
      })
      .finally(() => {
        setLoadingConfig(false);
      });
  }, []);

  if (loadingConfig) {
    return <Loader message="Initializing application..." />;
  }

  if (!googleClientId) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div style={{
          backgroundColor: '#1e293b',
          padding: '30px',
          borderRadius: '12px',
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
          border: '1px solid #334155',
          maxWidth: '500px'
        }}>
          <h2 style={{ color: '#f87171', marginBottom: '15px', marginTop: 0 }}>Configuration Missing</h2>
          <p style={{ color: '#94a3b8', lineHeight: '1.6', fontSize: '15px', margin: 0 }}>
            Google OAuth <strong>Client ID</strong> was not found. Please verify that <code>GOOGLE_CLIENT_ID</code> is configured in your AWS Secrets Manager or local <code>.env</code> settings.
          </p>
        </div>
      </div>
    );
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hr"
              element={
                <ProtectedRoute>
                  <HRDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
