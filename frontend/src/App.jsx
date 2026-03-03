import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AuthLayout from './layout/AuthLayout'
import MainLayout from './layout/MainLayout'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import Dashboard from './pages/student/Dashboard'
import Practice from './pages/student/Practice'
import Profile from './pages/student/Profile'
import LLMTest from './pages/student/LLMTest'
import LLMTest2 from './pages/student/LLMTest2'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Route>

          <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/LLMTest" element={<LLMTest />} />
            <Route path="/LLMTest2" element={<LLMTest2 />} />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
