import { useState } from 'react'
import apiClient from '../lib/api'
import { useAuthStore } from '../lib/store'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { setUser, setToken } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const payload = new URLSearchParams()
      payload.append('username', email)
      payload.append('password', password)

      const response = await apiClient.post('/auth/login', payload, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })

      const { access_token } = response.data
      console.log('Received access token:', access_token)
      setToken(access_token)

      // 3. Lấy profile và truyền thẳng token (đề phòng store chưa cập nhật kịp)
      const userResponse = await apiClient.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${access_token}`
        }
      })
      setUser(userResponse.data)

      navigate('/dashboard')
    } catch (err) {
      console.error('LỖI ĐÂY NÈ:', err)

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        const errorMessage = Array.isArray(detail)
          ? detail.map((item) => item.msg || JSON.stringify(item)).join(', ')
          : typeof detail === 'string'
          ? detail
          : JSON.stringify(detail)
        setError(errorMessage)
      } else {
        // Hiện lỗi JavaScript thực tế (Ví dụ: "apiClient is not defined", "navigate is not found"...)
        setError(err.message || 'Login failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md bg-white rounded-lg shadow p-8">
        <h1 className="text-3xl font-bold text-center mb-6">Login</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            onClick={(e) => {
              e.preventDefault();
              handleSubmit(e);
            }}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="text-center mt-4 text-gray-600">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-600 hover:underline">
            Register
          </a>
        </p>
      </div>
    </div>
  )
}
