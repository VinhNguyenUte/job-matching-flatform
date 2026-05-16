import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LogOut, Upload, Briefcase } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, [location.pathname]); 

  if (location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    navigate('/login');
  };

  return (
    <nav className="border-b bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold text-purple-600">JobMatch AI</Link>
        
        {isLoggedIn ? (
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="hover:text-purple-600 font-medium">Dashboard</Link>
            <Link to="/matches" className="hover:text-purple-600 font-medium flex items-center gap-1">
              <Briefcase size={18} /> Việc làm phù hợp
            </Link>
            <Link to="/cv-upload" className="hover:text-purple-600 font-medium flex items-center gap-1">
              <Upload size={18} /> Upload CV
            </Link>
            
            <button onClick={handleLogout} className="flex items-center gap-2 text-red-600 hover:text-red-700 transition font-medium">
              <LogOut size={18} /> Đăng xuất
            </button>
          </div>
        ) : (
          <Link to="/login" className="bg-purple-600 text-white px-6 py-2.5 rounded-xl hover:bg-purple-700 font-medium transition">
            Đăng nhập
          </Link>
        )}
      </div>
    </nav>
  );
}