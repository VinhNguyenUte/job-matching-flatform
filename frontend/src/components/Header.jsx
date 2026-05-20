import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/store'
import { Menu, X, Briefcase, LayoutDashboard, User, LogOut, LogIn, UserPlus } from 'lucide-react'
import { useState } from 'react'

export default function Header() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    setIsMenuOpen(false)
    navigate('/login')
  }

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-black tracking-tight text-blue-600 flex items-center gap-2">
          <span className="bg-blue-600 text-white px-2 py-0.5 rounded-lg text-xl">Job</span>Match
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link to="/jobs" className="text-gray-600 hover:text-blue-600 font-medium transition flex items-center gap-1.5">
            <Briefcase size={18} />
            Việc làm
          </Link>
          {user && (
            <>
              <Link to="/dashboard" className="text-gray-600 hover:text-blue-600 font-medium transition flex items-center gap-1.5">
                <LayoutDashboard size={18} />
                Gợi ý công việc
              </Link>
              <Link to="/profile" className="text-gray-600 hover:text-blue-600 font-medium transition flex items-center gap-1.5">
                <User size={18} />
                Hồ sơ & CV của tôi
              </Link>
            </>
          )}
        </div>

        <div className="hidden md:flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-4">
              <div className="flex flex-col text-right">
                <span className="text-sm font-semibold text-gray-900">{user.full_name || user.email}</span>
                <span className="text-xs text-green-600 font-medium">Ứng viên</span>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition flex items-center gap-2"
              >
                <LogOut size={16} />
                Đăng xuất
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition flex items-center gap-1.5"
              >
                <LogIn size={16} />
                Đăng nhập
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition flex items-center gap-1.5 shadow-sm"
              >
                <UserPlus size={16} />
                Đăng ký
              </Link>
            </div>
          )}
        </div>

        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="md:hidden p-2 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded-lg transition"
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </nav>

      {isMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 px-4 py-4 space-y-3 shadow-lg absolute w-full left-0 animate-in fade-in slide-in-from-top-2 duration-200">
          <Link 
            to="/jobs" 
            onClick={() => setIsMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg font-medium transition"
          >
            <Briefcase size={18} />
            Việc làm
          </Link>
          
          {user && (
            <>
              <Link 
                to="/dashboard" 
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg font-medium transition"
              >
                <LayoutDashboard size={18} />
                Gợi ý công việc
              </Link>
              <Link 
                to="/profile" 
                onClick={() => setIsMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg font-medium transition"
              >
                <User size={18} />
                Hồ sơ & CV của tôi
              </Link>
            </>
          )}

          <div className="border-t border-gray-100 pt-3 mt-1">
            {user ? (
              <div className="space-y-3">
                <div className="px-3 py-1 flex flex-col">
                  <span className="text-sm font-bold text-gray-800">{user.full_name || user.email}</span>
                  <span className="text-xs text-gray-500">Tài khoản ứng viên</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-sm font-medium text-red-600 border border-red-200 bg-red-50/50 rounded-lg hover:bg-red-50 transition flex items-center justify-center gap-2"
                >
                  <LogOut size={16} />
                  Đăng xuất
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 px-1">
                <Link
                  to="/login"
                  onClick={() => setIsMenuOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-center flex items-center justify-center gap-1.5"
                >
                  <LogIn size={16} />
                  Đăng nhập
                </Link>
                <Link
                  to="/register"
                  onClick={() => setIsMenuOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition text-center flex items-center justify-center gap-1.5"
                >
                  <UserPlus size={16} />
                  Đăng ký
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}