import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import AuditPage from './pages/AuditPage';
import AuditDetailPage from './pages/AuditDetailPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e2433',
              color: '#f1f5f9',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '10px',
              fontSize: '14px',
            },
            success: { iconTheme: { primary: '#22d3a5', secondary: '#0f1320' } },
            error:   { iconTheme: { primary: '#ef4444', secondary: '#0f1320' } },
          }}
        />
        <Routes>
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/chat"      element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/audit"     element={<AuditPage />} />
            <Route path="/audit/:traceId" element={<AuditDetailPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
