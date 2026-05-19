import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../lib/store'
import { Menu } from 'lucide-react'
import { useState } from 'react'

export default function Header() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="bg-white shadow">
      <nav className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold text-blue-600">
          JobMatch
        </Link>

        <div className="hidden md:flex gap-8">
          <Link to="/jobs" className="text-gray-700 hover:text-blue-600">
            Jobs
          </Link>
          {user && (
            <>
              <Link to="/dashboard" className="text-gray-700 hover:text-blue-600">
                Dashboard
              </Link>
              <Link to="/profile" className="text-gray-700 hover:text-blue-600">
                Profile
              </Link>
            </>
          )}
        </div>

        <div className="hidden md:flex gap-4">
          {user ? (
            <>
              <span className="text-gray-700">{user.full_name}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Register
              </Link>
            </>
          )}
        </div>

        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="md:hidden"
        >
          <Menu size={24} />
        </button>
      </nav>

      {isMenuOpen && (
        <div className="md:hidden bg-gray-50 px-4 py-4 space-y-4">
          <Link to="/jobs" className="block text-gray-700 hover:text-blue-600">
            Jobs
          </Link>
          {user && (
            <>
              <Link to="/dashboard" className="block text-gray-700 hover:text-blue-600">
                Dashboard
              </Link>
              <Link to="/profile" className="block text-gray-700 hover:text-blue-600">
                Profile
              </Link>
            </>
          )}
          {user ? (
            <button
              onClick={handleLogout}
              className="w-full px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
            >
              Logout
            </button>
          ) : (
            <>
              <Link
                to="/login"
                className="block px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50 text-center"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-center"
              >
                Register
              </Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}
