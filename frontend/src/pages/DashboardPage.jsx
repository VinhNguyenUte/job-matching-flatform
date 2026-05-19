import { useAuthStore } from '../lib/store'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  if (!user) {
    navigate('/login')
    return null
  }

  return (
    <div className="space-y-8">
      <h1 className="text-4xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stats Cards */}
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Applications</p>
          <p className="text-4xl font-bold">0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Saved Jobs</p>
          <p className="text-4xl font-bold">0</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Profile Views</p>
          <p className="text-4xl font-bold">0</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Recent Applications</h2>
        <p className="text-gray-600">No applications yet. Start exploring jobs!</p>
      </div>
    </div>
  )
}
