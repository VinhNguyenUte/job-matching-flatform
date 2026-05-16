import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CVUpload from './pages/CVUpload';
import Matches from './pages/Matches';
import { Toaster } from 'sonner';
import Register from './pages/Register';

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />; 
  }
  return children;
}

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="min-h-[calc(100vh-73px)]">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} /> */}
            <Route path="/dashboard" element={<Dashboard />} />

            {/* <Route path="/cv-upload" element={<ProtectedRoute><CVUpload /></ProtectedRoute>} /> */}
            <Route path="/cv-upload" element={<CVUpload />} />

            {/* <Route path="/matches" element={<ProtectedRoute><Matches /></ProtectedRoute>} /> */}
            <Route path="/matches" element={<Matches />} />

          </Routes>
        </main>
        <Toaster position="top-center" richColors />
      </div>
    </Router>
  );
}